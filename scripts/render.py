#!/usr/bin/env python3
"""Render the static pages from template.html + data.json.

Writes: index.html (Spanish, all meetings), en/index.html (English meetings),
sitemap.xml, robots.txt, llms.txt, CNAME.
Every meeting is written into the HTML itself so search engines and AI crawlers
can read it without running JavaScript; the page script then takes over.
"""
import json, os, re, html, math, datetime, urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://www.aamedellinmap.org"
DOMAIN = "www.aamedellinmap.org"

ORDER = ["L", "M", "Mc", "J", "V", "S", "D"]
EN_DAY = dict(zip(ORDER, ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]))
EN_SHORT = dict(zip(ORDER, ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]))
SCHEMA_DAY = {k: "https://schema.org/" + v for k, v in EN_DAY.items()}
ZONES = [("Centro", 6.2518, -75.5636), ("El Poblado", 6.2096, -75.5681), ("Laureles", 6.2456, -75.5916),
         ("Belén", 6.2320, -75.6010), ("Robledo", 6.2800, -75.5950), ("Manrique", 6.2690, -75.5540),
         ("Aranjuez", 6.2800, -75.5600), ("Castilla", 6.2920, -75.5750), ("Buenos Aires", 6.2380, -75.5540),
         ("Guayabal", 6.2180, -75.5880), ("San Javier", 6.2560, -75.6130), ("La América", 6.2520, -75.6010),
         ("Villa Hermosa", 6.2600, -75.5450), ("Envigado", 6.1700, -75.5900), ("Sabaneta", 6.1515, -75.6160),
         ("Itagüí", 6.1720, -75.6110)]

def esc(s):
    return html.escape(str(s or ""), quote=True)

def linkify(text):
    """Same rules as linkify() in template.html: URLs, emails, phones (Colombian mobiles → WhatsApp)."""
    h = esc(text)
    h = re.sub(r"\b((?:https?://|www\.)[^\s<]+[^\s<.,;:)])",
               lambda m: '<a href="%s" target="_blank" rel="noopener">%s</a>' % (m.group(1) if m.group(1).startswith("http") else "https://" + m.group(1), m.group(1)), h)
    h = re.sub(r"\b([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})\b", r'<a href="mailto:\1">\1</a>', h)
    def phone(m):
        raw = m.group(1); d = re.sub(r"\D", "", raw)
        if not raw.strip().startswith("+"):
            if len(d) == 10 and d.startswith("3"): d = "57" + d
            elif len(d) == 10: d = "1" + d
            else: return raw
        if len(d) < 10 or len(d) > 14: return raw
        if d.startswith("57") and d[2] == "3":
            return '<a class="wa" href="https://wa.me/%s" target="_blank" rel="noopener" title="WhatsApp">%s</a>' % (d, raw)
        return '<a href="tel:+%s">%s</a>' % (d, raw)
    return re.sub(r"(\+\s?\d[\d\s().-]{7,}\d|\b\d{3}[\s.-]\d{3}[\s.-]\d{4}\b)", phone, h)

def zone(m):
    mu = (m.get("municipio") or "").strip()
    if mu and mu.upper() != "MEDELLÍN":
        return (m["barrio"] + ", " + mu) if m.get("barrio") else mu
    if m.get("barrio"):
        return m["barrio"]
    txt = " ".join([m.get("name") or "", m.get("address") or "", m.get("place") or ""] + list(m.get("notes") or [])).lower().replace("centro comercial", "")
    for z in ZONES:
        if z[0].lower() in txt:
            return z[0]
    if m.get("lat") is None:
        return ""
    return min(ZONES, key=lambda z: (z[1] - m["lat"]) ** 2 + ((z[2] - m["lng"]) * math.cos(math.radians(6.2))) ** 2)[0]

def en_schedule(m, names=None):
    names = names or EN_SHORT
    out = []
    for t in m.get("times") or []:
        out.append(t if re.match(r"[A-Za-z]", t) else ", ".join(names[d] for d in m.get("days", [])) + " " + t)
    return "; ".join(out)

def to24(t):
    t = t.lower()
    if "noon" in t and not re.search(r"\d+:\d+\s*[ap]m", t):
        return "12:00"
    m = re.search(r"(\d{1,2})(?::(\d{2}))?\s*(am|pm|noon)", t)
    if not m:
        return None
    h, mi, ap = int(m.group(1)), int(m.group(2) or 0), m.group(3)
    if ap == "pm" and h != 12: h += 12
    if ap == "am" and h == 12: h = 0
    return "%02d:%02d" % (h, mi)

def day_codes_en(text):
    t = text.lower(); days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    out = []
    r = re.search(r"(%s)\s*(?:through|to|-|–)\s*(%s)" % ("|".join(days), "|".join(days)), t)
    if r:
        a, b = days.index(r.group(1)), days.index(r.group(2)); out += ORDER[a:b + 1]
    for i, d in enumerate(days):
        if re.search(r"\b" + d, t) and ORDER[i] not in out: out.append(ORDER[i])
    return out

def slots(m):
    """[(day_code, 'HH:MM'), ...] for an English/manual meeting."""
    res = []
    for t in m.get("times") or []:
        hhmm = to24(t)
        if not hhmm: continue
        ds = day_codes_en(t) or m.get("days", [])
        res += [(d, hhmm) for d in ds]
    return res

def fmt12(hhmm):
    h, mi = map(int, hhmm.split(":"))
    if h == 12 and mi == 0: return "12:00 noon"
    return "%d:%02d %s" % ((h - 1) % 12 + 1, mi, "am" if h < 12 else "pm")

# ------------------------------------------------------------------ cards
def card(m, T, lang="es"):
    en = m.get("lang") == "en"
    tags = []
    tg = T["tag"]
    if m.get("kind") == "12step": tags.append('<span class="tag ts" title="%s">%s</span>' % (esc(T["allprogTitle"]), T["allprog"]))
    if en: tags.append('<span class="tag en">%s</span>' % tg["english"])
    if m.get("topic"): tags.append('<span class="tag o">%s</span>' % esc(T["topic"].get(m["topic"], m["topic"])))
    if m.get("type"): tags.append('<span class="tag o">%s</span>' % tg[m["type"]])
    fmt = m.get("format")
    if fmt == "online": tags.append('<span class="tag o">%s</span>' % tg["online"])
    elif fmt == "hybrid": tags.append('<span class="tag o">%s</span>' % tg["hybrid"])
    elif m.get("virtual"): tags.append('<span class="tag o">%s</span>' % tg["virtual"])
    if m.get("approx") and m.get("lat") is not None:
        tags.append('<span class="tag o" title="%s">≈ %s</span>' % (esc(T["approxTitle"]), T["approx"]))
    addr = " · ".join(x for x in [m.get("place"), m.get("address"), m.get("detail")] if x)
    sched = en_schedule(m, dict(T["days"])) if "times" in m else (m.get("schedule_" + lang) or m.get("schedule") or T["nosched"])
    contact = " · ".join(x for x in [m.get("contact"), m.get("email")] if x)
    gm = m.get("map") or ("https://www.google.com/maps/search/?api=1&query=%s,%s" % (m["lat"], m["lng"]) if m.get("lat") is not None else "")
    parts = ['<article class="card%s">' % (" ts" if m.get("kind") == "12step" else ""), '<h2>%s %s</h2>' % (esc(m["name"]), " ".join(tags))]
    if addr: parts.append('<div class="addr">%s</div>' % esc(addr))
    z = zone(m)
    if z: parts.append('<div class="zone">%s</div>' % esc(z))
    parts.append('<div class="hor">%s</div>' % esc(sched))
    if m.get("notes"): parts.append('<div class="notes">%s</div>' % "<br>".join(linkify(n) for n in m["notes"]))
    if m.get("zoom"): parts.append('<div class="notes">%s</div>' % linkify(m["zoom"]))
    if contact: parts.append('<div class="notes">%s: %s</div>' % (T["contact"], linkify(contact)))
    links = []
    if fmt != "online" and (m.get("lat") is not None or m.get("address")):
        dest = (", ".join(x for x in [m.get("place"), m.get("address")] if x) + ", Medellín, Antioquia, Colombia") if (en or m.get("lat") is None) else "%s,%s" % (m["lat"], m["lng"])
        links.append('<a class="dir" href="https://www.google.com/maps/dir/?api=1&amp;destination=%s" target="_blank" rel="noopener">%s</a>' % (urllib.parse.quote(dest), T["directions"]))
    if gm and fmt != "online": links.append('<a href="%s" target="_blank" rel="noopener">Google Maps</a>' % esc(gm))
    if m.get("url"): links.append('<a href="%s" target="_blank" rel="noopener">%s</a>' % (esc(m["url"]), T["website"] if m.get("source") == "manual" else T["source"]))
    parts.append('<div class="links">%s</div>' % "".join(links))
    parts.append("</article>")
    return "\n".join(parts)

# ------------------------------------------------------------------ structured data
def place_ld(m):
    p = {"@type": "Place", "name": m.get("place") or m["name"]}
    if m.get("address"):
        p["address"] = {"@type": "PostalAddress", "streetAddress": m["address"], "addressLocality": (m.get("municipio") or "Medellín"),
                        "addressRegion": "Antioquia", "addressCountry": "CO"}
    if m.get("lat") is not None:
        p["geo"] = {"@type": "GeoCoordinates", "latitude": m["lat"], "longitude": m["lng"]}
    return p

def event_ld(m, lang):
    ev = {"@type": "Event", "name": m["name"] + (" (English-speaking AA meeting)" if lang == "en" else " (Alcohólicos Anónimos)"),
          "inLanguage": "en" if lang == "en" else "es", "isAccessibleForFree": True,
          "organizer": {"@type": "Organization", "name": m["name"]}}
    fmt = m.get("format") or ("online" if m.get("virtual") and str(m.get("schedule", "")).lower().startswith("virtual") else "in-person")
    ev["eventAttendanceMode"] = {"online": "https://schema.org/OnlineEventAttendanceMode",
                                 "hybrid": "https://schema.org/MixedEventAttendanceMode"}.get(fmt, "https://schema.org/OfflineEventAttendanceMode")
    if fmt == "online":
        ev["location"] = {"@type": "VirtualLocation", "url": m.get("url") or SITE}
    else:
        ev["location"] = place_ld(m)
    desc = [m.get("topic"), (m.get("type") or "").capitalize() + " meeting" if m.get("type") else "", en_schedule(m) if "times" in m else m.get("schedule")]
    ev["description"] = ". ".join(x for x in desc if x)
    sl = slots(m) if "times" in m else []
    if sl:
        by = {}
        for d, t in sl: by.setdefault(t, []).append(SCHEMA_DAY[d])
        ev["eventSchedule"] = [{"@type": "Schedule", "repeatFrequency": "P1W", "byDay": ds, "startTime": t,
                                "scheduleTimezone": "America/Bogota"} for t, ds in by.items()]
    if sl:
        base = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=-5)))
        nxt = []
        for d, t in sl:
            ahead = (ORDER.index(d) - base.weekday()) % 7
            h, mi = map(int, t.split(":"))
            dt = (base + datetime.timedelta(days=ahead)).replace(hour=h, minute=mi, second=0, microsecond=0)
            if dt < base: dt += datetime.timedelta(days=7)
            nxt.append(dt)
        ev["startDate"] = min(nxt).isoformat()
        ev["eventStatus"] = "https://schema.org/EventScheduled"
    if m.get("url"): ev["url"] = m["url"]
    return ev

def group_ld(m):
    ev = {"@type": "Event", "name": m["name"] + " (Alcohólicos Anónimos)", "inLanguage": "es", "isAccessibleForFree": True,
          "organizer": {"@type": "Organization", "name": m["name"]},
          "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode", "location": place_ld(m),
          "description": "Grupo de AA. Horario: " + (m.get("schedule_es") or m.get("schedule") or "no publicado")}
    sched = []
    for sg in m.get("slots") or []:
        days = [SCHEMA_DAY[d] for d in sg["days"] if d in SCHEMA_DAY]
        for t in sg["times"]:
            if days:
                sched.append({"@type": "Schedule", "repeatFrequency": "P1W", "byDay": days, "startTime": t["start"], "scheduleTimezone": "America/Bogota"})
    if sched: ev["eventSchedule"] = sched
    if m.get("url"): ev["url"] = m["url"]
    return ev

# ------------------------------------------------------------------ strings
ES = dict(LANG="es", OGLOCALE="es_CO", CANON="/", DATA="data.json", DEFAULT_FILTER="all",
    TITLE="AA en Medellín: mapa y horarios de reuniones de Alcohólicos Anónimos",
    H1="Reuniones de AA en Medellín",
    T_LANG="Idioma", T_ALL="Todos", T_SEARCH="Buscar nombre, dirección o barrio", T_DAY="Día", T_FMT="Modalidad",
    T_ALLF="Todas", T_INPERSON="Presencial", T_ONLINE="Virtual", T_NEAR="Cerca de", T_BYNAME="Ordenar por nombre",
    T_MAP="Mapa de reuniones", T_ADDR="Dirección u hotel", T_ADDR_PH="Escribe tu dirección u hotel para ordenar por distancia", T_ADDR_GO="Buscar", T_LEG_EN="Reunión en inglés", T_LEG_ES="Grupo en español", T_LEG_MIX="Ambos en el mismo lugar",
    BRAND="AA Medellín Map",
    LANGSW='<span lang="es">ES</span><a href="en/" hreflang="en" lang="en">EN</a>')
EN = dict(LANG="en", OGLOCALE="en_US", CANON="/en/", DATA="../data.json", DEFAULT_FILTER="en",
    TITLE="English-Speaking AA Meetings in Medellín, Colombia: Map and Schedule",
    H1="English-Speaking AA Meetings in Medellín",
    T_LANG="Language", T_ALL="All", T_SEARCH="Search name, address or neighborhood", T_DAY="Day", T_FMT="Format",
    T_ALLF="All", T_INPERSON="In person", T_ONLINE="Online", T_NEAR="Near", T_BYNAME="Sort by name",
    T_MAP="Meeting map", T_ADDR="Address or hotel", T_ADDR_PH="Type your address or hotel to sort by distance", T_ADDR_GO="Go", T_LEG_EN="English-speaking meeting", T_LEG_ES="Spanish-language group", T_LEG_MIX="Both at the same venue",
    BRAND="AA Medellín Map",
    LANGSW='<a href="../" hreflang="es" lang="es">ES</a><span lang="en">EN</span>')
TOPIC_ES = {"Big Book Study": "Estudio del Libro Grande", "AA Big Book Study": "Estudio del Libro Grande",
            "12 & 12 Step/Tradition Study": "Estudio de Pasos y Tradiciones", "Open AA 12×12 Study": "Estudio de los Doce y Doce",
            "Open Speaker Meeting": "Reunión de oradores"}
TJS = {
 "es": {"allprog": "Todos los programas de 12 pasos", "allprogTitle": "Reunión abierta de 12 pasos: bienvenidos miembros de AA, NA, Al-Anon y cualquier programa de 12 pasos",
        "website": "Sitio web", "addrNeedsGoogle": "Por ahora la búsqueda por dirección exacta no está disponible; escribe el nombre del hotel, un parque o un punto conocido.",
        "addrOk": "Ordenado por distancia desde:", "addrFail": "No encontramos esa dirección. Prueba con el nombre del hotel o agrega el barrio.",
        "approx": "ubicación aproximada", "approxTitle": "El pin se colocó a partir de la dirección y puede estar a una cuadra de distancia. Usa 'Cómo llegar' para la ruta exacta.",
        "myloc": "📍 Mi ubicación", "metro": "Área metropolitana", "byname": "Ordenar por nombre", "locating": "Buscando tu ubicación…", "locfail": "No se pudo obtener tu ubicación","directions": "Cómo llegar", "details": "Ver detalles", "topic": TOPIC_ES,
        "tag": {"english": "Inglés", "open": "abierta", "closed": "cerrada", "online": "solo virtual", "hybrid": "híbrida", "virtual": "virtual"},"locale": "es-CO", "updated": "Actualizado: ", "empty": "Ningún grupo coincide con esos filtros.", "contact": "Contacto",
        "onmap": "Ver en el mapa", "source": "Fuente", "loadfail": "No se pudo cargar la lista.", "nosched": "Horario no publicado",
        "days": [["L", "Lun"], ["M", "Mar"], ["Mc", "Mié"], ["J", "Jue"], ["V", "Vie"], ["S", "Sáb"], ["D", "Dom"]]},
 "en": {"allprog": "All 12-step programs welcome", "allprogTitle": "Open 12-step meeting: AA, NA, Al-Anon and any 12-step program welcome",
        "website": "Website", "addrNeedsGoogle": "Exact street-number search isn't available yet; type the hotel name, a park or a known landmark.",
        "addrOk": "Sorted by distance from:", "addrFail": "Couldn't find that address. Try the hotel name or add the neighborhood.",
        "approx": "approx. location", "approxTitle": "This pin was placed from the address and may be off by a block. Use Directions for the exact route.",
        "myloc": "📍 My location", "metro": "Metro area", "byname": "Sort by name", "locating": "Finding your location…", "locfail": "Couldn't get your location",
        "directions": "Directions", "details": "Details", "topic": {},
        "tag": {"english": "English", "open": "open", "closed": "closed", "online": "online only", "hybrid": "hybrid", "virtual": "online"},
        "locale": "en-US", "updated": "Updated: ", "empty": "No meetings match those filters.", "contact": "Contact",
        "onmap": "Show on map", "source": "Source", "loadfail": "Couldn't load the meeting list.", "nosched": "Schedule not published",
        "days": [["L", "Mon"], ["M", "Tue"], ["Mc", "Wed"], ["J", "Thu"], ["V", "Fri"], ["S", "Sat"], ["D", "Sun"]]},
}

SITECFG = {}
def render():
    global SITECFG
    try: SITECFG = json.load(open(os.path.join(ROOT, "site.json"), encoding="utf-8"))
    except Exception: SITECFG = {}
    tpl = open(os.path.join(ROOT, "template.html"), encoding="utf-8").read()
    d = json.load(open(os.path.join(ROOT, "data.json"), encoding="utf-8"))
    manual = [m for m in d.get("manual", []) if not m.get("hidden")]
    en_list = d["en"] + [m for m in manual if m.get("lang") == "en"]
    es_list = d["es"] + [m for m in manual if m.get("lang") != "en"]
    upd = datetime.datetime.strptime(d["updated"], "%Y-%m-%dT%H:%M:%SZ")
    n_en_sessions = len({(m["name"], s) for m in en_list for s in slots(m)})
    en_zones = sorted({zone(m) for m in en_list if zone(m)})
    has_online = any(m.get("format") in ("online", "hybrid") for m in en_list)

    # weekly English table
    rows = []
    for dcode in ORDER:
        items = sorted(((t, m) for m in en_list for (dd, t) in slots(m) if dd == dcode), key=lambda x: x[0])
        if not items: continue
        cell = "<br>".join("%s · %s%s" % (fmt12(t), esc(m["name"]), (" · " + esc(zone(m))) if zone(m) else " · online")
                           for t, m in items)
        rows.append("<tr><th>%s</th><td>%s</td></tr>" % (EN_DAY[dcode], cell))
    en_table = '<section class="sched"><h2>Weekly schedule</h2><div class="tw"><table>%s</table></div></section>' % "".join(rows)
    es_table = en_table.replace("Weekly schedule", "Reuniones en inglés por día")

    disclaimer_es = ("Sitio independiente, sin afiliación con Alcoholics Anonymous World Services, AA Colombia ni los grupos listados. "
                     "Los datos se actualizan a diario desde <a href=\"https://aacolombia.org/grupos/\" target=\"_blank\" rel=\"noopener\">aacolombia.org</a> y "
                     "<a href=\"https://aamedellin.org/meetings/\" target=\"_blank\" rel=\"noopener\">aamedellin.org</a>; confirma el horario antes de ir. "
                     "Distancias en línea recta; las ubicaciones de las reuniones en inglés son aproximadas.")
    disclaimer_en = ("Independent site, not affiliated with Alcoholics Anonymous World Services, AA Colombia or the groups listed. "
                     "Data is refreshed daily from <a href=\"https://aamedellin.org/meetings/\" target=\"_blank\" rel=\"noopener\">aamedellin.org</a> and "
                     "<a href=\"https://aacolombia.org/grupos/\" target=\"_blank\" rel=\"noopener\">aacolombia.org</a>; confirm before you go. "
                     "Map pins for English meetings are approximate.")

    pages = {
     "es": dict(ES, CARDS=sorted(es_list + en_list, key=lambda m: m["name"]), SCHEDULE=es_table,
        DESC="Mapa y horarios de %d grupos de Alcohólicos Anónimos en Medellín y %d reuniones de AA en inglés. Filtra por día, barrio y modalidad. Actualizado a diario." % (len(es_list), len(en_list)),
        INTRO='<p class="intro">Hay %d grupos de Alcohólicos Anónimos en Medellín según el directorio de AA Colombia, y %d reuniones en inglés en El Poblado, Laureles y Sabaneta. Usa el mapa o los filtros para encontrar una reunión hoy. <a href="en/">English meetings →</a></p>' % (len(es_list), len(en_list)),
        SRC="Fuentes: aacolombia.org y aamedellin.org.", NOTE=disclaimer_es,
        COUNT="%d grupos" % (len(es_list) + len(en_list)), UPDATED="Actualizado: %s." % upd.strftime("%d/%m/%Y")),
     "en": dict(EN, CARDS=en_list, SCHEDULE=en_table,
        DESC="Every English-speaking AA meeting in Medellín, Colombia: %d meetings a week in %s%s, with map, addresses, times and contacts. Updated daily." % (n_en_sessions, ", ".join(en_zones), " and online" if has_online else ""),
        INTRO='<p class="intro">There are %d English-speaking Alcoholics Anonymous meetings each week in Medellín, Colombia, in %s%s. Below is every meeting with its address, time, contact and a map. The list is refreshed daily from aamedellin.org. Spanish-language groups (%d) are listed too; switch to "All" to see them. <a href="../">Versión en español →</a></p>' % (n_en_sessions, ", ".join(en_zones), ", plus online meetings on Zoom" if has_online else "", len(es_list)),
        SRC="Sources: aamedellin.org and aacolombia.org.", NOTE=disclaimer_en,
        COUNT="%d meetings" % len(en_list), UPDATED="Updated %s." % upd.strftime("%b %d, %Y")),
    }

    for lang, P in pages.items():
        T = TJS[lang]
        ld = {"@context": "https://schema.org", "@graph": [
            {"@type": "WebSite", "name": "AA Medellín Map", "url": SITE + "/", "inLanguage": ["es", "en"]},
            {"@type": "WebPage", "name": P["TITLE"], "url": SITE + P["CANON"], "description": P["DESC"],
             "inLanguage": lang, "dateModified": d["updated"], "about": {"@type": "Thing", "name": "Alcoholics Anonymous meetings in Medellín"}},
        ] + [event_ld(m, "en") for m in en_list] + ([group_ld(m) for m in es_list] if lang == "es" else [])}
        out = tpl
        rep = {k: v for k, v in P.items() if k not in ("CARDS",)}
        rep["GMAPS_KEY"] = SITECFG.get("google_maps_key", "")
        rep.update(TITLE=esc(P["TITLE"]), DESC=esc(P["DESC"]), CANONICAL=SITE + P["CANON"], SITE=SITE,
                   JSONLD=json.dumps(ld, ensure_ascii=False).replace("</", "<\\/"),
                   STATIC_LIST="\n".join(card(m, T, lang) for m in P["CARDS"]), TJS=json.dumps(T, ensure_ascii=False))
        for k, v in rep.items():
            out = out.replace("{{%s}}" % k, str(v))
        left = re.findall(r"\{\{[A-Z_]+\}\}", out)
        assert not left, left
        path = os.path.join(ROOT, "index.html" if lang == "es" else "en/index.html")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        open(path, "w", encoding="utf-8").write(out)

    day = upd.strftime("%Y-%m-%d")
    open(os.path.join(ROOT, "sitemap.xml"), "w").write(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
        + "".join('<url><loc>%s%s</loc><lastmod>%s</lastmod><changefreq>daily</changefreq>'
                  '<xhtml:link rel="alternate" hreflang="es" href="%s/"/><xhtml:link rel="alternate" hreflang="en" href="%s/en/"/></url>\n'
                  % (SITE, p, day, SITE, SITE) for p in ("/", "/en/"))
        + "</urlset>\n")
    open(os.path.join(ROOT, "robots.txt"), "w").write(
        "User-agent: *\nAllow: /\n\n"
        "# AI search and assistant crawlers are welcome\n"
        + "".join("User-agent: %s\nAllow: /\n\n" % b for b in
                  ["GPTBot", "OAI-SearchBot", "ChatGPT-User", "ClaudeBot", "Claude-SearchBot", "Claude-User",
                   "PerplexityBot", "Perplexity-User", "Google-Extended", "Applebot-Extended", "Bingbot"])
        + "Sitemap: %s/sitemap.xml\n" % SITE)

    L = ["# AA Medellín Map", "",
         "> Independent, daily-updated directory of Alcoholics Anonymous meetings in Medellín, Colombia: %d Spanish-language groups (from AA Colombia's directory, aacolombia.org) and %d English-speaking meetings (from aamedellin.org and local listings). Not affiliated with AA." % (len(es_list), len(en_list)),
         "", "Last updated: %s" % day, "",
         "- [English-speaking AA meetings in Medellín](%s/en/): map, weekly schedule, addresses and contacts" % SITE,
         "- [Reuniones de AA en Medellín (español)](%s/): all groups with map and filters" % SITE,
         "- [Raw data (JSON)](%s/data.json)" % SITE, "", "## English-speaking meetings", ""]
    for m in en_list:
        where = " · ".join(x for x in [m.get("place"), m.get("address")] if x) or "Online (Zoom)"
        bits = [en_schedule(m), (m.get("type") or "") + (" meeting" if m.get("type") else ""), m.get("topic"), m.get("format"), where,
                ("Contact: " + m["contact"]) if m.get("contact") else ""]
        L.append("- **%s**: %s" % (m["name"], "; ".join(b for b in bits if b)))
    L += ["", "## Weekly English schedule", ""]
    for dcode in ORDER:
        items = sorted(((t, m) for m in en_list for (dd, t) in slots(m) if dd == dcode), key=lambda x: x[0])
        if items:
            L.append("- %s: %s" % (EN_DAY[dcode], "; ".join("%s %s" % (fmt12(t), m["name"]) for t, m in items)))
    L += ["", "## Spanish-language groups", "",
          "%d groups across Medellín; full list with addresses and schedules at %s/ and in %s/data.json." % (len(es_list), SITE, SITE), ""]
    open(os.path.join(ROOT, "llms.txt"), "w", encoding="utf-8").write("\n".join(L))
    open(os.path.join(ROOT, "CNAME"), "w").write(DOMAIN + "\n")

if __name__ == "__main__":
    render()
    print("rendered")
