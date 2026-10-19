#!/usr/bin/env python3
"""Rebuild data.json from aacolombia.org (Spanish groups) and aamedellin.org (English meetings).

Run from the repo root:  python3 scripts/build.py
If a source is unreachable or parses badly, the previous data for that source is kept.
"""
import os, json, re, html, sys, unicodedata, datetime, urllib.request, urllib.parse

ROOT = __import__("os").path.dirname(__import__("os").path.dirname(__import__("os").path.abspath(__file__)))
OUT = f"{ROOT}/data.json"
MANUAL = f"{ROOT}/manual.json"
VENUES = f"{ROOT}/venues.json"
MUNICIPIOS = {"MEDELLIN", "BELLO", "ENVIGADO", "ITAGUI", "SABANETA"}   # municipalities included on the map
UA = {"User-Agent": "aa-medellin-directory/1.0 (+https://github.com/apollodeus/aa-medellin)"}

def get(url, timeout=60):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "ignore")

def norm(s):
    return unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().upper().strip()

SMALL = {"y", "e", "o", "u", "de", "del", "la", "las", "el", "los", "a", "al", "en", "con", "por", "para", "sin"}
def nice_name(n):
    if n != n.upper():
        return n
    words = n.lower().split()
    out = []
    for i, w in enumerate(words):
        if i and w in SMALL:
            out.append(w)
        elif w in ("aa", "a.a."):
            out.append(w.upper())
        else:
            out.append(w[:1].upper() + w[1:])
    return " ".join(out)

def load_json(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

# ---------------------------------------------------------------- Spanish groups
def fetch_spanish():
    rows = []
    for page in range(1, 60):
        url = ("https://aacolombia.org/wp-json/wp/v2/grupos?per_page=100&page=%d"
               "&_fields=id,title,link,spectra_custom_meta" % page)
        try:
            data = json.loads(get(url))
        except Exception as e:
            if page == 1:
                raise
            break
        if not isinstance(data, list) or not data:
            break
        for g in data:
            m = g.get("spectra_custom_meta") or {}
            f = lambda k: html.unescape(((m.get(k) or [""])[0] or "")).strip()
            if norm(f("municipio")) not in MUNICIPIOS:
                continue
            if f("activo") == "false":
                continue
            lat = f("coordenadas_gps_lat") or f("grupo_coordenada_lat")
            lng = f("coordenadas_gps_lng") or f("grupo_coordenada_lng")
            rows.append({
                "id": "es-%s" % g["id"],
                "lang": "es",
                "name": nice_name(html.unescape(g["title"]["rendered"]).strip()),
                "address": f("direccion"),
                "detail": f("detalle"),
                "barrio": f("barrio"),
                "municipio": f("municipio").title().replace("Itagüí", "Itagüí"),
                "schedule": f("horario"),
                "virtual": f("virtual") == "true",
                "link": f("transmision") if f("transmision").startswith("http") else "",
                "link_note": "" if f("transmision").startswith("http") else f("transmision"),
                "link_password": f("transmision_password"),
                "info": "" if f("informacion_adicional") in ("", "(null)") else f("informacion_adicional"),
                "contact": f("contacto"),
                "email": f("correo_electronico"),
                "lat": float(lat) if lat else None,
                "lng": float(lng) if lng else None,
                "url": g["link"],
                "source": "aacolombia.org",
            })
        if len(data) < 100:
            break
    return rows

# ---------------------------------------------------------------- English meetings
DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
DAY_CODE = dict(zip(DAYS, ["L", "M", "Mc", "J", "V", "S", "D"]))

def day_codes(text):
    t = text.lower()
    out = []
    m = re.search(r"(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\s*(?:–|-|through|to)\s*(monday|tuesday|wednesday|thursday|friday|saturday|sunday)", t)
    if m:
        a, b = DAYS.index(m.group(1)), DAYS.index(m.group(2))
        out += [DAY_CODE[d] for d in DAYS[a:b + 1]]
    for d in DAYS:
        if re.search(r"\b" + d + r"s?\b", t) and DAY_CODE[d] not in out:
            out.append(DAY_CODE[d])
    return out

def fetch_english(venues):
    h = get("https://aamedellin.org/meetings/")
    # the schedule lives in the text-editor widget that contains "Clean Living"
    i = h.find("Clean Living")
    i = h.rfind('elementor-widget-container', 0, i)
    j = h.find("</div>", i)
    blk = h[i:j]
    lines = []
    for p in re.findall(r"<p>(.*?)</p>", blk, re.S):
        t = re.sub(r'<a [^>]*href="([^"]+)"[^>]*>.*?</a>', r" \1 ", p)
        bold = bool(re.search(r"<(b|strong)>", t))
        t = html.unescape(re.sub(r"<[^>]+>", " ", t))
        t = re.sub(r"\s+", " ", t).strip()
        if t:
            lines.append((bold, t))

    meetings, cur, days = [], None, []
    def flush():
        if cur:
            meetings.append(cur)
    for bold, t in lines:
        if bold:
            if "//" in t:  # "Monday – Friday // Clean Living (Zoom Only)"
                flush(); dpart, name = t.split("//", 1)
                days = day_codes(dpart)
                cur = {"name": name.strip(), "days": list(days), "lines": []}
            elif t.lower().rstrip("s") in DAYS or day_codes(t) and len(t.split()) <= 3:
                flush(); cur = None; days = day_codes(t)
            else:
                flush(); cur = {"name": t.strip(), "days": list(days), "lines": []}
        elif cur is not None:
            cur["lines"].append(t)
    flush()

    out = []
    for m in meetings:
        rec = {"id": "", "lang": "en", "name": m["name"], "days": m["days"], "times": [],
               "type": "", "format": "", "address": "", "place": "", "notes": [],
               "contact": "", "zoom": "", "map": "", "source": "aamedellin.org",
               "url": "https://aamedellin.org/meetings/", "lat": None, "lng": None}
        for t in m["lines"]:
            tl = t.lower()
            if re.search(r"\d{1,2}(:\d{2})?\s*(am|pm|noon)", tl):
                tt = re.sub(r"\s*local time", "", t, flags=re.I)
                tt = re.sub(r"^(open|closed)\s+meeting\s*", "", tt, flags=re.I).strip()
                rec["times"].append(tt)
                extra = day_codes(t)
                for d in extra:
                    if d not in rec["days"]:
                        rec["days"].append(d)
                if "closed" in tl: rec["type"] = "closed"
                if "open" in tl and not rec["type"]: rec["type"] = "open"
                continue
            if re.match(r"(map link|map:)", tl):
                rec["map"] = re.search(r"https?://\S+", t).group(0) if re.search(r"https?://\S+", t) else ""
                continue
            if tl.startswith("contact"):
                rec["contact"] = re.sub(r"^contact:?\s*", "", t, flags=re.I).replace("mailto:", "").strip(); continue
            if "zoom id" in tl:
                rec["zoom"] = t; continue
            if tl.startswith("http://bit.ly") or tl.startswith("https://bit.ly"):
                rec["zoom"] = (rec["zoom"] + " " + t).strip(); continue
            if tl.startswith("address:"):
                rec["address"] = t.split(":", 1)[1].strip(); continue
            if tl.startswith("place:"):
                rec["place"] = t.split(":", 1)[1].strip(); continue
            if re.match(r"(cra\.?|carrera|calle|cl\.?)\s*\d", tl) and not rec["address"]:
                rec["address"] = t; continue
            if "closed meeting" in tl: rec["type"] = "closed"; continue
            if "open" in tl and "meeting" in tl and not rec["type"]: rec["type"] = "open"
            if "hybrid" in tl: rec["format"] = "hybrid"; continue
            if "zoom only" in tl: rec["format"] = "online"; continue
            rec["notes"].append(t)
        if "zoom only" in m["name"].lower():
            rec["format"] = "online"
        if not rec["format"]:
            rec["format"] = "in-person"
        rec["notes"] = [n for n in rec["notes"] if n]
        if not rec["address"] and rec["notes"]:
            # Sabaneta-style listing: venue then address lines
            for n in rec["notes"]:
                if re.match(r"(cra\.?|carrera|calle|cl\.?)\s*\d", n.lower()):
                    rec["address"] = n; rec["notes"].remove(n); break
        rec["topic"] = ""
        for n in list(rec["notes"]):
            if re.search(r"\b(study|speaker|discussion|meditation)\b", n, re.I) and len(n) < 50 and not rec["topic"]:
                rec["topic"] = n; rec["notes"].remove(n)
        if not rec["type"] and re.search(r"\bopen\b", rec["topic"], re.I): rec["type"] = "open"
        rec["notes"] = [n for n in rec["notes"] if not re.match(r"^(open|closed) (aa )?meeting\.?$", n, re.I)]
        if not rec["place"] and rec["notes"] and rec["format"] != "online":
            if not re.search(r"\b(go|proceed|walk|take|ask)\b", rec["notes"][0], re.I) and len(rec["notes"][0]) < 60:
                rec["place"] = rec["notes"].pop(0)
        rec["notes"] = [re.sub(r"\s*\(?GSO Approved\s*https?://\S+\s*\)?", " (GSO approved)", n).strip() for n in rec["notes"]]
        rec["id"] = "en-" + re.sub(r"[^a-z0-9]+", "-", (rec["name"] + "-" + "".join(rec["days"])).lower()).strip("-")
        # merge with an earlier entry of the same group at the same place
        same = next((o for o in out if o["name"] == rec["name"] and o["address"] == rec["address"] and o.get("topic") == rec.get("topic")), None)
        if same:
            for d in rec["days"]:
                if d not in same["days"]: same["days"].append(d)
            for t in rec["times"]:
                if t not in same["times"]: same["times"].append(t)
            same["days"].sort(key=["L","M","Mc","J","V","S","D"].index)
            same["id"] = "en-" + re.sub(r"[^a-z0-9]+", "-", (same["name"] + "-" + "".join(same["days"])).lower()).strip("-")
            continue
        out.append(rec)
    return out

# ---------------------------------------------------------------- main
def main():
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import geocode as G
    prev = load_json(OUT, {"es": [], "en": [], "manual": []})
    venues = load_json(VENUES, [])
    status, report = {}, []
    prev_es, prev_en = len(prev.get("es", [])), len(prev.get("en", []))

    try:
        es = fetch_spanish()
        if len(es) < 50 or (prev_es and len(es) < 0.7 * prev_es):
            raise RuntimeError("only %d Spanish groups parsed (previously %d)" % (len(es), prev_es))
        status["es"] = "ok"
    except Exception as e:
        es = prev.get("es", []); status["es"] = "kept previous (%s)" % e
    try:
        en = fetch_english(venues)
        if len(en) < 4 or (prev_en and len(en) < 0.6 * prev_en):
            raise RuntimeError("only %d English meetings parsed (previously %d)" % (len(en), prev_en))
        status["en"] = "ok"
    except Exception as e:
        en = prev.get("en", []); status["en"] = "kept previous (%s)" % e

    overrides = load_json(os.path.join(ROOT, "overrides.json"), {})
    for rec in es + en:
        fix = overrides.get(rec["id"])
        if fix:
            rec.update(fix)

    # Spanish groups: official coordinates, sanity-checked; schedules parsed into slots
    import schedule as SCH
    kept = []
    for r in es:
        segs = SCH.parse(r.get("schedule", ""))
        r["slots"] = segs
        r["schedule_es"] = SCH.format(segs, "es") if segs else r.get("schedule", "")
        r["schedule_en"] = SCH.format(segs, "en") if segs else r.get("schedule", "")
        sch = (r.get("schedule") or "").strip().lower()
        online_only = bool(re.match(r"(reuniones\s+)?virtual", sch))
        if online_only and not r["link"]:
            zid = re.search(r"zoom\s*id\s*(?:de\s*reuni[oó]n)?\s*:?\s*(\d[\d\s]{7,}\d)", sch)
            if zid:
                r["link"] = "https://zoom.us/j/" + re.sub(r"\D", "", zid.group(1))
            pw = re.search(r"(?:contrase[ñn]a|password|clave|c[oó]digo)\s*:?\s*(\S+)", sch)
            if pw and not r["link_password"]:
                r["link_password"] = pw.group(1)
        r["format"] = "online" if online_only else ("hybrid" if (r["virtual"] or r["link"]) else "in-person")
        if online_only:
            r["address"] = ""; r["detail"] = ""; r["lat"] = None; r["lng"] = None
        if not segs and r.get("schedule"):
            report.append("schedule not understood (shown as written): %s — \"%s\"" % (r["name"], r["schedule"]))
        if r["lat"] is not None and not G.in_bbox(r["lat"], r["lng"]):
            report.append("dropped, outside the Medellín area (%s): %s — %s — %s" % (r.get("detail") or r["address"], r["name"], r["address"], r["url"]))
            continue
        if r["lat"] is None:
            G.place(r, venues, report)
        else:
            r["approx"] = False; r["pin_source"] = "aacolombia.org"
            G.audit_official(r, report)
        kept.append(r)
    es = kept

    for rec in en:
        G.place(rec, venues, report)

    manual = load_json(MANUAL, [])
    for i, m in enumerate(manual):
        m.setdefault("id", "manual-%d" % i)
        m.setdefault("source", "manual")
        if not m.get("hidden"):
            G.place(m, venues, report)
    G.save_cache()

    for k, v in status.items():
        if v != "ok":
            report.insert(0, "SOURCE PROBLEM (%s): %s" % (k, v))
    for msg in G.GOOGLE_ERRORS:
        report.insert(0, "GOOGLE GEOCODING ERROR — pins fell back to estimates: " + msg)
    if not G.GOOGLE_KEY:
        report.append("note: GOOGLE_GEOCODING_KEY is not set, so addresses are pinned from map links and hand-placed estimates only")

    data = {
        "updated": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "status": status, "es": es, "en": en, "manual": manual,
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    with open(os.path.join(ROOT, "report.md"), "w", encoding="utf-8") as f:
        f.write("# Build report\n\nUpdated %s. Sources: %s. %d Spanish groups, %d English meetings, %d manual.\n\n"
                % (data["updated"], json.dumps(status), len(es), len(en), len(manual)))
        f.write("\n".join("- " + line for line in report) if report else "No issues.")
        f.write("\n")
    print(json.dumps(status), len(es), "es", len(en), "en", len(manual), "manual;", len(report), "report lines")
    import render
    render.render()

if __name__ == "__main__":
    main()
