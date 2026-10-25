"""Write meetingguide.json: the site's meetings in Meeting Guide API format (the feed format the
Meeting Guide app and aa.org consume). One entry per meeting per day and start time.

Only AA meetings go in: entries with kind "12step" (open to all programs) are left out.
Spec: https://github.com/code4recovery/spec
"""
import json, os, re, unicodedata, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://www.aamedellinmap.org"
DAY_NUM = {"D": 0, "L": 1, "M": 2, "Mc": 3, "J": 4, "V": 5, "S": 6}   # Meeting Guide: 0 = Sunday
TOPIC_TYPES = [
    (r"big book|libro grande", "BB"), (r"speaker|orador", "SP"), (r"12 ?& ?12|12x12|step|pasos", "ST"),
    (r"tradition|tradici", "TR"), (r"beginner|principiante", "BE"), (r"meditaci|meditation", "MED"),
    (r"literature|literatura", "LIT"),
]

def slugify(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")

def hhmm_plus(hhmm, minutes=60):
    h, m = map(int, hhmm.split(":"))
    t = (h * 60 + m + minutes) % (24 * 60)
    return "%02d:%02d" % (t // 60, t % 60)

def types_for(m, note=""):
    t = []
    t.append("EN" if m.get("lang") == "en" else "S")
    if m.get("type") == "open": t.append("O")
    elif m.get("type") == "closed": t.append("C")
    fmt = m.get("format") or "in-person"
    if fmt == "online": t.append("ONL")
    elif fmt == "hybrid": t.append("HY")
    hay = " ".join([m.get("topic") or "", note or ""]).lower()
    for pat, code in TOPIC_TYPES:
        if re.search(pat, hay) and code not in t:
            t.append(code)
    nl = note.lower()
    if "cerrada" in nl and "C" not in t: t.append("C")
    if ("virtual" in nl or "online" in nl) and fmt == "hybrid": pass
    return t

def address_fields(m):
    fmt = m.get("format") or "in-person"
    if fmt == "online":
        return {}
    city = m.get("municipio") or "Medellín"
    street = re.sub(r",\s*(medell[ií]n|antioquia|colombia)\s*$", "", (m.get("address") or ""), flags=re.I).strip()
    street = re.sub(r",\s*(medell[ií]n|antioquia|colombia)\s*$", "", street, flags=re.I).strip()
    out = {"location": m.get("place") or m["name"], "address": street, "city": city,
           "state": "Antioquia", "country": "CO",
           "formatted_address": ", ".join(x for x in [street, city, "Antioquia", "Colombia"] if x)}
    if m.get("lat") is not None:
        out["latitude"], out["longitude"] = m["lat"], m["lng"]
    notes = [x for x in [m.get("detail"), m.get("barrio") and ("Barrio " + m["barrio"])] if x]
    if notes:
        out["location_notes"] = ". ".join(notes)
    return out

def build(data):
    updated = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=-5))).strftime("%Y-%m-%d %H:%M:%S")
    out, seen, skipped = [], set(), []
    manual = [m for m in data.get("manual", []) if not m.get("hidden") and m.get("kind") != "12step"]
    for m in data["es"] + data["en"] + manual:
        if m.get("kind") == "12step":
            continue
        slots = m.get("slots") or []
        for sg in slots:
            for t in sg["times"]:
                if not t.get("start"):
                    continue
                for d in sg["days"]:
                    if d not in DAY_NUM:
                        continue
                    slug = slugify("%s-%s-%s-%s" % (m["name"], m.get("municipio") or "medellin", d, t["start"].replace(":", "")))
                    if slug in seen:
                        continue
                    seen.add(slug)
                    e = {"name": m["name"], "slug": slug, "day": DAY_NUM[d], "time": t["start"],
                         "end_time": t.get("end") or hhmm_plus(t["start"]), "timezone": "America/Bogota",
                         "types": types_for(m, sg.get("note", "")), "updated": updated,
                         "group": m["name"], "region": m.get("municipio") or "Medellín",
                         "url": SITE + ("/en/" if m.get("lang") == "en" else "/")}
                    e.update(address_fields(m))
                    if "formatted_address" not in e and not m.get("link"):
                        skipped.append(m["name"]); continue
                    if m.get("link"):
                        e["conference_url"] = m["link"]
                        if m.get("link_password"):
                            e["conference_url_notes"] = "Contraseña / password: " + m["link_password"]
                    notes = [sg.get("note") or ""]
                    if m.get("lang") == "en":
                        notes += m.get("notes") or []
                        if m.get("zoom"): notes.append(m["zoom"])
                    else:
                        if m.get("info"): notes.append(m["info"])
                        if m.get("link_note"): notes.append(m["link_note"])
                    notes = [n for n in notes if n]
                    if notes:
                        e["notes"] = " ".join(notes)
                    contact = " · ".join(x for x in [m.get("contact"), m.get("email")] if x)
                    if contact:
                        e["group_notes"] = "Contacto / contact: " + contact
                    if m.get("source") == "aacolombia.org" and m.get("url"):
                        e["edit_url"] = m["url"]
                    out.append(e)
    out.sort(key=lambda e: (e["day"], e["time"], e["name"]))
    return out, sorted(set(skipped))

def write(data):
    feed, skipped = build(data)
    with open(os.path.join(ROOT, "meetingguide.json"), "w", encoding="utf-8") as f:
        json.dump(feed, f, ensure_ascii=False, indent=1)
    return len(feed), skipped

if __name__ == "__main__":
    d = json.load(open(os.path.join(ROOT, "data.json"), encoding="utf-8"))
    n, skipped = write(d)
    print(n, "meeting entries; skipped (no address and no public link):", skipped)
