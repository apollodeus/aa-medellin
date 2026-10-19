"""Parse aacolombia.org schedule text into structured slots, and format them per language.

Input styles seen in the data:
  "LMcV 7pm D 5pm"                     codes: L M Mc J V S D (+F festivos)
  "Lunes, Miércoles y Viernes 7:30 pm; Domingo 10:00 am"
  "Lunes a Sábado 7:00 pm" / "Todos los días 7:00 pm; Domingos 9:00 am."
  "LMMcJVSD 6:30pm-7:15pm y 7:30pm-8:30pm" / "de 9:00 am a 12: m."
  "Lunes a Viernes 8pm - Martes y Viernes 7pm (Principiantes) - Sábados 6 pm"
Output: [{"days": ["L","Mc","V"], "times": [{"start": "19:00", "end": None}], "note": ""}, ...]
"""
import re

ORDER = ["L", "M", "Mc", "J", "V", "S", "D"]
NAMES = {"lunes": "L", "martes": "M", "miercoles": "Mc", "jueves": "J", "viernes": "V", "sabado": "S", "domingo": "D", "festivo": "F"}
NAME_RE = r"(lunes|martes|mi[eé]rcoles|jueves|viernes|s[aá]bados?|domingos?|festivos?)"
CODE_RE = r"(?:Mc|L|M|J|V|S|D|F)+"
TIME_RE = r"\d{1,2}\s*\+?\s*(?::\s*(?:\d{2}|oo)?)?\s*(?:a\.?\s?m\.?|p\.?\s?m\.?|m\.?|M\b|noon)?"
NOTE_WORDS = r"(reuni[oó]n de principiantes|principiantes|cerrada|abierta|virtual(?:es)?|presencial(?:es)?)"
MONTHLY_RE = r"(primer|segundo|tercer|cuarto|[uú]ltimo)\s+" + NAME_RE + r"\s+de(?:l)?\s+mes"

def _norm(s):
    s = s.replace(" ", " ")
    s = re.sub(r"[…]", "", s)
    return s

def _time(tok, default_mer=None):
    """'7pm' / '6+:30 pm' / '12:oo' / '12:15m' -> ('19:00', 'pm')"""
    t = tok.lower().replace(" ", "").replace("+", "").replace("oo", "00")
    t = re.sub(r":(?=[apmn]|$)", "", t)
    m = re.match(r"(\d{1,2})(?::(\d{2}))?(a\.?m\.?|p\.?m\.?|m\.?|noon)?$", t)
    if not m:
        return None, None
    h, mi, mer = int(m.group(1)), int(m.group(2) or 0), m.group(3)
    if mer:
        mer = "am" if mer.startswith("a") else ("pm" if mer.startswith("p") else "noon")
    if mer == "noon" or (mer is None and h == 12 and default_mer is None):
        mer = "pm"
    if mer is None:
        mer = default_mer or ("am" if 6 <= h <= 11 else "pm")
    if mer == "pm" and h != 12:
        h += 12
    if mer == "am" and h == 12:
        h = 0
    if h > 23 or mi > 59:
        return None, None
    return "%02d:%02d" % (h, mi), mer

def parse(text):
    if not text:
        return []
    s = _norm(text)
    long_form = bool(re.search(NAME_RE + r"|todos los d", s, re.I))
    segs, cur_days, cur_times, cur_note, pending_days = [], [], [], [], []

    def flush():
        nonlocal cur_days, cur_times, cur_note
        if cur_days and cur_times:
            segs.append({"days": [d for d in ORDER if d in cur_days] + (["F"] if "F" in cur_days else []),
                         "times": cur_times, "note": " ".join(cur_note).strip()})
        cur_days, cur_times, cur_note = [], [], []

    # tokenizer
    tok_re = re.compile(
        r"(?P<range>%s\s*(?:,\s*)?-\s*%s)" % (TIME_RE, TIME_RE) +
        r"|(?P<range2>(?:de\s+)?%s\s+a\s+%s)" % (TIME_RE, TIME_RE) +
        r"|(?P<time>%s)" % TIME_RE +
        r"|(?P<monthly>%s)" % MONTHLY_RE +
        r"|(?P<all>todos los d[ií]as|diario|lunes a domingo)" +
        r"|(?P<dayrange>%s\s+a\s+%s)" % (NAME_RE, NAME_RE) +
        r"|(?P<day>%s)" % NAME_RE +
        (r"|(?P<code>\b%s\b)" % CODE_RE if not long_form else r"|(?P<code>\b(?:(?:Mc|L|M|J|V|S|D|F){2,}|(?:Mc|L|M|J|V|S|D|F)(?=\s*\d))\b)") +
        r"|(?P<paren>\([^)]*\))" +
        r"|(?P<note>%s)" % NOTE_WORDS +
        r"|(?P<sep>[;/]|\s-\s|\.\s)" +
        r"|(?P<word>\S+)", re.I)
    last_mer = None
    for m in tok_re.finditer(s):
        k = m.lastgroup; v = m.group(0)
        if k in ("all", "dayrange", "day", "code", "monthly"):
            if cur_times:
                flush()
            if k == "monthly":
                cur_days.append(NAMES[_strip(re.findall(NAME_RE, v, re.I)[0])]); cur_note.append(v)
            elif k == "all":
                cur_days += ORDER
            elif k == "dayrange":
                a, b = re.findall(NAME_RE, v, re.I)
                a, b = NAMES[_strip(a)], NAMES[_strip(b)]
                ia, ib = ORDER.index(a), ORDER.index(b)
                cur_days += ORDER[ia:ib + 1] if ia <= ib else ORDER[ia:] + ORDER[:ib + 1]
            elif k == "day":
                cur_days.append(NAMES[_strip(v)])
            else:
                cur_days += re.findall(r"Mc|L|M|J|V|S|D|F", v)
        elif k in ("range", "range2", "time"):
            if not cur_days and segs and not cur_times:
                # a time with no day before it (e.g. "7:00 pm y 7:30 pm"): belongs to the previous days
                cur_days = list(segs[-1]["days"]); cur_note = [segs[-1]["note"]] if segs[-1]["note"] else []
                cur_times = list(segs[-1]["times"]); segs.pop()
            if k == "time":
                st, mer = _time(v, None)
                if st:
                    last_mer = mer
                    cur_times.append({"start": st, "end": None})
            else:
                parts = re.findall(TIME_RE, v)
                parts = [p for p in parts if p.strip()]
                if len(parts) >= 2:
                    a, b = parts[0], parts[-1]
                    b_explicit = re.search(r"[ap]\.?\s?m|noon|\bm\b", b.lower())
                    if b_explicit:
                        eb, mb = _time(b, None)
                        ea, ma = _time(a, mb)
                    else:
                        ea, ma = _time(a, None)
                        eb, mb = _time(b, ma)
                        if ea and eb and eb <= ea:
                            eb, mb = _time(b, "pm" if ma == "am" else "am")
                    if ea and eb:
                        last_mer = mb
                        cur_times.append({"start": ea, "end": eb})
        elif k == "paren":
            inner = v.strip("()").strip()
            if re.search(TIME_RE, inner) and not re.search(NOTE_WORDS, inner, re.I):
                continue
            cur_note.append(inner)
        elif k == "note":
            cur_note.append(v)
        elif k == "sep":
            if cur_times:
                flush()
        else:
            w = v.lower().strip(",.")
            if w in ("y", ",", "de", "a", "las", "la", "reuniones", "reunion", "reunión", "hora", "horario", "e", "lunes"):
                continue
            if cur_times and re.match(r"[a-záéíóú]", w):
                cur_note.append(v.strip(",."))
    flush()
    # merge consecutive identical day sets
    out = []
    for sg in segs:
        if out and out[-1]["days"] == sg["days"] and out[-1]["note"] == sg["note"]:
            out[-1]["times"] += [t for t in sg["times"] if t not in out[-1]["times"]]
        else:
            out.append(sg)
    return out

def _strip(name):
    n = name.lower().replace("é", "e").replace("á", "a")
    for k in NAMES:
        if n.startswith(k):
            return k
    return n

def days_of(segs):
    return sorted({d for sg in segs for d in sg["days"] if d != "F"}, key=ORDER.index)

# ---------------------------------------------------------------- formatting
LABELS = {
    "es": {"L": "Lun", "M": "Mar", "Mc": "Mié", "J": "Jue", "V": "Vie", "S": "Sáb", "D": "Dom", "F": "Festivos",
           "all": "Todos los días", "range": "%s a %s", "and": " y ", "noon": "12:00 m", "sep": " · "},
    "en": {"L": "Mon", "M": "Tue", "Mc": "Wed", "J": "Thu", "V": "Fri", "S": "Sat", "D": "Sun", "F": "Holidays",
           "all": "Every day", "range": "%s to %s", "and": " and ", "noon": "12:00 noon", "sep": " · "},
}
NOTE_TR = {"principiantes": "beginners", "cerrada": "closed", "abierta": "open", "virtuales": "online", "virtual": "online",
           "presenciales": "in person", "presencial": "in person", "reunión de principiantes": "beginners meeting",
           "primer jueves de mes": "first Thursday of the month", "festivos no hay reunión": "no meeting on holidays"}

def fmt12(hhmm, lang):
    h, mi = map(int, hhmm.split(":"))
    if h == 12 and mi == 0:
        return LABELS[lang]["noon"]
    return "%d:%02d %s" % ((h - 1) % 12 + 1, mi, "am" if h < 12 else "pm")

def _days_label(days, lang):
    L = LABELS[lang]
    wk = [d for d in days if d != "F"]
    fest = "F" in days
    if wk == ORDER:
        lab = L["all"]
    elif len(wk) >= 3 and all(ORDER.index(wk[i + 1]) == ORDER.index(wk[i]) + 1 for i in range(len(wk) - 1)):
        lab = L["range"] % (L[wk[0]], L[wk[-1]])
    elif len(wk) > 1:
        lab = ", ".join(L[d] for d in wk[:-1]) + L["and"] + L[wk[-1]]
    elif wk:
        lab = L[wk[0]]
    else:
        lab = ""
    if fest:
        if len(wk) > 1 and lab.count(L["and"].strip()) and " a " not in lab and " to " not in lab:
            lab = lab.replace(L["and"], ", ", 1) + L["and"] + L["F"]
        else:
            lab = (lab + L["and"] if lab else "") + L["F"]
    return lab

def format(segs, lang):
    out = []
    for sg in segs:
        times = []
        for t in sg["times"]:
            times.append(fmt12(t["start"], lang) + ("–" + fmt12(t["end"], lang) if t["end"] else ""))
        note = sg["note"]
        if lang == "en" and note:
            note = NOTE_TR.get(note.lower(), note)
        piece = _days_label(sg["days"], lang) + " " + (LABELS[lang]["and"].strip().join(" " + x + " " for x in times).strip() if len(times) > 1 else (times[0] if times else ""))
        if note:
            piece += " (%s)" % note
        out.append(piece.strip())
    return LABELS[lang]["sep"].join(out)

if __name__ == "__main__":
    import json, sys, os
    d = json.load(open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data.json"), encoding="utf-8"))
    bad = 0
    for r in d["es"]:
        segs = parse(r["schedule"])
        if not segs:
            bad += 1
        print(("OK " if segs else "?? ") + r["schedule"][:70].ljust(70), "=>", format(segs, "es"), "|", format(segs, "en"))
    print(bad, "unparsed of", len(d["es"]))
