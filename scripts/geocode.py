"""Pin placement for meetings, from most to least trustworthy:

1. A confirmed pin in venues.json ("approx": false)       - a person checked it
2. Coordinates inside the meeting's own Google Maps link   - the organizer's pin
2b. The building/business name (rec["place"]) looked up on Google - best evidence when the listing names one
3. Google Geocoding API, rooftop/range precision           - needs GOOGLE_GEOCODING_KEY
4. An approximate pin in venues.json                       - hand-placed estimate
5. Nominatim (OpenStreetMap), street-level only            - rough, marked approx

Results are cached in geocache.json so each address is looked up once.
"""
import json, os, re, time, math, urllib.request, urllib.parse, urllib.error, unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_PATH = os.path.join(ROOT, "geocache.json")
UA = {"User-Agent": "aa-medellin-map/1.0 (+https://github.com/apollodeus/aa-medellin)"}
# Aburrá valley: anything outside this is not a Medellín-area meeting
BBOX = (6.08, 6.42, -75.72, -75.45)
GOOGLE_KEY = os.environ.get("GOOGLE_GEOCODING_KEY", "").strip()

_cache = None
def cache():
    global _cache
    if _cache is None:
        try:
            _cache = json.load(open(CACHE_PATH, encoding="utf-8"))
        except Exception:
            _cache = {}
    return _cache

def save_cache():
    if _cache is not None:
        json.dump(_cache, open(CACHE_PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=1, sort_keys=True)

def norm(s):
    return unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().upper().strip()

def in_bbox(lat, lng):
    return lat is not None and BBOX[0] < lat < BBOX[1] and BBOX[2] < lng < BBOX[3]

def km(a, b, c, d):
    x = (c - a) * math.pi / 180
    y = (d - b) * math.pi / 180 * math.cos((a + c) / 2 * math.pi / 180)
    return 6371 * math.sqrt(x * x + y * y)

def _get(url, timeout=25):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.geturl(), r.read().decode("utf-8", "ignore")

# ---------------------------------------------------------------- 2. Google Maps links
_COORD_PATTERNS = [
    r"@(-?\d{1,2}\.\d{4,}),(-?\d{1,3}\.\d{4,})",
    r"[?&]q=(-?\d{1,2}\.\d{4,}),(-?\d{1,3}\.\d{4,})",
    r"!3d(-?\d{1,2}\.\d{4,})!4d(-?\d{1,3}\.\d{4,})",
    r"[?&]ll=(-?\d{1,2}\.\d{4,}),(-?\d{1,3}\.\d{4,})",
]
def coords_from_maplink(url):
    """Follow a maps.app.goo.gl / share link and pull coordinates if the final URL carries them."""
    if not url:
        return None
    key = "link:" + url
    c = cache()
    if key in c:
        v = c[key]
        return (v["lat"], v["lng"]) if v else None
    result = None
    try:
        final, _ = _get(url)
        for pat in _COORD_PATTERNS:
            m = re.search(pat, final)
            if m:
                lat, lng = float(m.group(1)), float(m.group(2))
                if in_bbox(lat, lng):
                    result = (lat, lng)
                break
    except Exception:
        pass
    c[key] = {"lat": result[0], "lng": result[1], "source": "maplink"} if result else None
    return result

# ---------------------------------------------------------------- 3. Google Geocoding
GOOGLE_ERRORS = []
def clean_address(a):
    """Drop office/floor/building suffixes that confuse geocoders: 'Carrera 49 No. 50-58 - Of. 308 - Ed. San Fernando' -> 'Carrera 49 No. 50-58'."""
    a = re.split(r"\s*[-,(]\s*(?:of(?:icina)?\.?|piso|local|ed(?:ificio)?\.?|apto|torre|segundo piso|primer piso|tercer piso)\b", a, 1, flags=re.I)[0]
    m = re.search(r"\b(calle|carrera|cra\.?|cr\.?|cl\.?|cll\.?|diagonal|dg\.?|transversal|tv\.?|avenida|av\.?|circular|cq\.?)\s*\d", a, re.I)
    if m and m.start() > 0:
        a = a[m.start():]          # drop leading descriptions like "Local Parroquial-"
    return a.strip(" -,")

def google_geocode(address, city="Medellín", hint=""):
    if not GOOGLE_KEY or not address:
        return None
    address = clean_address(address)
    key = "google:" + norm(address) + ("" if norm(city) == "MEDELLIN" else " | " + norm(city)) + (" | " + norm(hint) if hint else "")
    c = cache()
    if key in c:
        v = c[key]
        return (v["lat"], v["lng"], v["precise"]) if v else None
    result, status = None, "EXCEPTION"
    try:
        q = urllib.parse.urlencode({"address": address + (", " + hint if hint else "") + ", %s, Antioquia, Colombia" % city,
                                    "components": "country:CO", "region": "co", "language": "es",
                                    "bounds": "%s,%s|%s,%s" % (BBOX[0], BBOX[2], BBOX[1], BBOX[3]),
                                    "key": GOOGLE_KEY})
        _, body = _get("https://maps.googleapis.com/maps/api/geocode/json?" + q)
        data = json.loads(body)
        status = data.get("status", "?")
        if status not in ("OK", "ZERO_RESULTS"):
            msg = "%s: %s" % (status, data.get("error_message", ""))
            if msg not in GOOGLE_ERRORS:
                GOOGLE_ERRORS.append(msg)
            return None          # do not cache a failed call
        for res in data.get("results", []):
            loc = res["geometry"]["location"]
            lt = res["geometry"].get("location_type", "")
            if not in_bbox(loc["lat"], loc["lng"]):
                continue
            precise = lt in ("ROOFTOP", "RANGE_INTERPOLATED")
            result = (loc["lat"], loc["lng"], precise)
            break
    except Exception as e:
        msg = "EXCEPTION: %s" % e
        if msg not in GOOGLE_ERRORS:
            GOOGLE_ERRORS.append(msg)
        return None
    c[key] = {"lat": result[0], "lng": result[1], "precise": result[2], "source": "google"} if result else None
    return result

PLACE_TYPES = {"establishment", "point_of_interest", "premise", "shopping_mall", "church", "place_of_worship", "school",
               "hospital", "university", "library", "city_hall", "local_government_office", "lodging", "store", "subpremise"}
def google_place(name, city="Medellín"):
    """Look up a building/business name ('Galerías de San Diego') with Places API (New) text search - the same search
    Google Maps itself uses, so local names and English/Spanish variants both work. Falls back to the Geocoding API
    (which only knows a few landmarks) when Places is not enabled. Only a named-place match counts, never a street or area."""
    if not GOOGLE_KEY or not name:
        return None
    key = "place:" + norm(name) + " | " + norm(city)
    c = cache()
    if key in c:
        v = c[key]
        return (v["lat"], v["lng"]) if v else None
    result = None
    # 1. Places API (New) text search
    try:
        body = json.dumps({"textQuery": "%s, %s, Antioquia, Colombia" % (name, city), "languageCode": "es", "regionCode": "CO",
                           "pageSize": 3,
                           "locationRestriction": {"rectangle": {"low": {"latitude": BBOX[0], "longitude": BBOX[2]},
                                                                 "high": {"latitude": BBOX[1], "longitude": BBOX[3]}}}}).encode()
        req = urllib.request.Request("https://places.googleapis.com/v1/places:searchText", data=body, method="POST",
                                     headers={**UA, "Content-Type": "application/json", "X-Goog-Api-Key": GOOGLE_KEY,
                                              "X-Goog-FieldMask": "places.displayName,places.location,places.types,places.formattedAddress"})
        with urllib.request.urlopen(req, timeout=25) as r:
            data = json.loads(r.read().decode("utf-8", "ignore"))
        for pl in data.get("places", []):
            loc = pl["location"]
            if in_bbox(loc["latitude"], loc["longitude"]) and not ({"route", "locality", "sublocality", "neighborhood", "political"} >= set(pl.get("types", []))):
                result = (loc["latitude"], loc["longitude"]); break
        c[key] = {"lat": result[0], "lng": result[1], "source": "google places", "query": name} if result else None
        return result
    except urllib.error.HTTPError as e:
        try:
            err = json.loads(e.read().decode("utf-8", "ignore")).get("error", {})
            msg = "PLACES %s: %s" % (err.get("status"), (err.get("message") or "")[:160])
        except Exception:
            msg = "PLACES HTTP %s" % e.code
        if msg not in GOOGLE_ERRORS: GOOGLE_ERRORS.append(msg)
    except Exception as e:
        msg = "PLACES EXCEPTION: %s" % e
        if msg not in GOOGLE_ERRORS: GOOGLE_ERRORS.append(msg)
    # 2. fallback: Geocoding API, named-place results only
    try:
        q = urllib.parse.urlencode({"address": "%s, %s, Antioquia, Colombia" % (name, city), "components": "country:CO",
                                    "region": "co", "language": "es",
                                    "bounds": "%s,%s|%s,%s" % (BBOX[0], BBOX[2], BBOX[1], BBOX[3]), "key": GOOGLE_KEY})
        _, body = _get("https://maps.googleapis.com/maps/api/geocode/json?" + q)
        data = json.loads(body)
        if data.get("status") not in ("OK", "ZERO_RESULTS"):
            msg = "%s: %s" % (data.get("status"), data.get("error_message", ""))
            if msg not in GOOGLE_ERRORS: GOOGLE_ERRORS.append(msg)
            return None
        for res in data.get("results", []):
            loc = res["geometry"]["location"]
            if in_bbox(loc["lat"], loc["lng"]) and PLACE_TYPES & set(res.get("types", [])) and not res.get("partial_match"):
                result = (loc["lat"], loc["lng"]); break
    except Exception as e:
        msg = "EXCEPTION: %s" % e
        if msg not in GOOGLE_ERRORS: GOOGLE_ERRORS.append(msg)
        return None
    c[key] = {"lat": result[0], "lng": result[1], "source": "google geocoder (place)"} if result else None
    return result

# ---------------------------------------------------------------- 5. Nominatim (street level)
_last_nominatim = 0.0
def nominatim(address):
    """Street-level only: Nominatim does not know Colombian house numbers. Always approximate."""
    global _last_nominatim
    if not address:
        return None
    street = re.split(r"\s*(?:#|No\.?|N°|Nro\.?)\s*", address, 1)[0]
    street = re.sub(r"\s+\d+[A-Za-z]*\s*-\s*\d+.*$", "", street).strip(" ,")
    if not street:
        return None
    key = "osm:" + norm(street)
    c = cache()
    if key in c:
        v = c[key]
        return (v["lat"], v["lng"]) if v else None
    result = None
    try:
        wait = 1.2 - (time.time() - _last_nominatim)
        if wait > 0:
            time.sleep(wait)
        _last_nominatim = time.time()
        q = urllib.parse.urlencode({"q": street + ", Medellín, Colombia", "format": "json", "limit": 1,
                                    "viewbox": "%s,%s,%s,%s" % (BBOX[2], BBOX[1], BBOX[3], BBOX[0]), "bounded": 1})
        _, body = _get("https://nominatim.openstreetmap.org/search?" + q)
        for res in json.loads(body):
            lat, lng = float(res["lat"]), float(res["lon"])
            if in_bbox(lat, lng):
                result = (lat, lng)
                break
    except Exception:
        pass
    c[key] = {"lat": result[0], "lng": result[1], "source": "osm"} if result else None
    return result

# ---------------------------------------------------------------- venues.json
def venue_match(rec, venues):
    hay = norm(" ".join([rec.get("address", ""), rec.get("place", ""), rec.get("name", "")] + list(rec.get("notes", []))))
    for v in venues:
        if all(norm(k) in hay for k in v["match"]):
            return v
    return None

# ---------------------------------------------------------------- main entry
def place(rec, venues, report):
    """Fill rec['lat'], rec['lng'], rec['approx'], rec['pin_source']. Returns nothing."""
    v = venue_match(rec, venues)
    if v and v.get("place") and not rec.get("place"):
        rec["place"] = v["place"]
    full_addr = ", ".join(x for x in [rec.get("place"), rec.get("address")] if x)

    # explicit coordinates in manual.json are a person's own pin
    if rec.get("source") == "manual" and rec.get("lat") is not None:
        rec["approx"] = False; rec["pin_source"] = "manual"; return

    if v and v.get("approx") is False:
        rec["lat"], rec["lng"], rec["approx"], rec["pin_source"] = v["lat"], v["lng"], False, "venues.json (confirmed)"; return

    hit = coords_from_maplink(rec.get("map"))
    if hit:
        rec["lat"], rec["lng"], rec["approx"], rec["pin_source"] = hit[0], hit[1], False, "organizer map link"; return

    pl = google_place(rec.get("place"), rec.get("municipio") or "Medellín") if rec.get("place") else None
    if pl:
        ga = google_geocode(rec.get("address"), rec.get("municipio") or "Medellín", rec.get("barrio") or "") if rec.get("address") else None
        if ga and km(pl[0], pl[1], ga[0], ga[1]) > 1.5:
            report.append("named place '%s' matched %.1f km from the address, address used instead (check): %s" % (rec["place"], km(pl[0], pl[1], ga[0], ga[1]), rec["name"]))
        else:
            rec["lat"], rec["lng"], rec["approx"], rec["pin_source"] = pl[0], pl[1], False, "google place (%s)" % rec["place"]; return

    g = google_geocode(full_addr, rec.get("municipio") or "Medellín", rec.get("barrio") or "")
    if g and g[2]:
        rec["lat"], rec["lng"], rec["approx"], rec["pin_source"] = g[0], g[1], False, "google geocoder"; return

    if v:
        rec["lat"], rec["lng"], rec["approx"], rec["pin_source"] = v["lat"], v["lng"], True, "venues.json (approx)"
        report.append("approx pin (hand-placed estimate): %s — %s" % (rec["name"], full_addr)); return

    if g:
        rec["lat"], rec["lng"], rec["approx"], rec["pin_source"] = g[0], g[1], True, "google geocoder (imprecise)"
        report.append("approx pin (geocoder could not match the house number): %s — %s" % (rec["name"], full_addr)); return

    n = nominatim(rec.get("address"))
    if n:
        rec["lat"], rec["lng"], rec["approx"], rec["pin_source"] = n[0], n[1], True, "openstreetmap street"
        report.append("approx pin (street only): %s — %s" % (rec["name"], full_addr)); return

    if rec.get("format") != "online":
        report.append("NO PIN: %s — %s" % (rec["name"], full_addr or "(no address)"))

def audit_official(rec, report):
    """Spanish group with official coordinates: the written address wins. Geocode it (with the barrio hint);
    if a precise result lands more than 120 m from the official pin, move the pin to the address and report it.
    Only exception: the hinted and unhinted geocodes disagree with each other (ambiguous address) - keep the official pin."""
    if not GOOGLE_KEY or rec.get("lat") is None or not rec.get("address"):
        return
    city = rec.get("municipio") or "Medellín"
    pl = google_place(rec.get("place"), city) if rec.get("place") else None
    if pl:
        d = km(rec["lat"], rec["lng"], pl[0], pl[1])
        ga = google_geocode(rec["address"], city, rec.get("barrio") or "")
        if d > 1.5 and (not ga or km(pl[0], pl[1], ga[0], ga[1]) > 1.5):
            report.append("named place '%s' matched %.1f km from both the official pin and the address, not used (check): %s — %s" % (rec["place"], d, rec["name"], rec["url"]))
            pl = None
    if pl:
        if d > 0.12:
            report.append("pin moved %d m to the named place '%s' (official pin disagreed): %s — %s" % (round(d * 1000), rec["place"], rec["name"], rec["url"]))
            rec["lat"], rec["lng"], rec["approx"], rec["pin_source"] = pl[0], pl[1], False, "google place (%s)" % rec["place"]
        return
    g = google_geocode(rec["address"], city, rec.get("barrio") or "")
    if not (g and g[2]):
        return
    d = km(rec["lat"], rec["lng"], g[0], g[1])
    if d <= 0.12:
        return
    g2 = google_geocode(rec["address"], city, "")
    if g2 and g2[2] and km(g[0], g[1], g2[0], g2[1]) > 0.3:
        report.append("address is ambiguous to the geocoder, official pin kept (check): %s — %s — %s" % (rec["name"], rec["address"], rec["url"]))
        return
    report.append("pin moved %d m to the written address (official pin disagreed): %s — %s — %s" % (round(d * 1000), rec["name"], rec["address"], rec["url"]))
    rec["lat"], rec["lng"], rec["approx"], rec["pin_source"] = g[0], g[1], False, "google geocoder (official pin was %d m off)" % round(d * 1000)
