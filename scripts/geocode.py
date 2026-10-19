"""Pin placement for meetings, from most to least trustworthy:

1. A confirmed pin in venues.json ("approx": false)       - a person checked it
2. Coordinates inside the meeting's own Google Maps link   - the organizer's pin
3. Google Geocoding API, rooftop/range precision           - needs GOOGLE_GEOCODING_KEY
4. An approximate pin in venues.json                       - hand-placed estimate
5. Nominatim (OpenStreetMap), street-level only            - rough, marked approx

Results are cached in geocache.json so each address is looked up once.
"""
import json, os, re, time, math, urllib.request, urllib.parse, unicodedata

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
def google_geocode(address):
    if not GOOGLE_KEY or not address:
        return None
    key = "google:" + norm(address)
    c = cache()
    if key in c:
        v = c[key]
        return (v["lat"], v["lng"], v["precise"]) if v else None
    result, status = None, "EXCEPTION"
    try:
        q = urllib.parse.urlencode({"address": address + ", Medellín, Antioquia, Colombia",
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

    g = google_geocode(full_addr)
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
    """For a Spanish group with official coordinates: compare against the geocoded address when a key is set."""
    if not GOOGLE_KEY or rec.get("lat") is None or not rec.get("address"):
        return
    g = google_geocode(rec["address"])
    if g and g[2]:
        d = km(rec["lat"], rec["lng"], g[0], g[1])
        if d > 0.4:
            report.append("official pin is %.1f km from its address (check): %s — %s — %s" % (d, rec["name"], rec["address"], rec["url"]))
