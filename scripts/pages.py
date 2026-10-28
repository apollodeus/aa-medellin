"""Extra pages rendered from page.html: the newcomer's guide in Spanish (/primera-reunion/) and English (/en/first-meeting/)."""
import json, os, re, html

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://www.aamedellinmap.org"
esc = lambda s: html.escape(str(s), quote=True)

ES_PATH, EN_PATH = "/primera-reunion/", "/en/first-meeting/"

PREAMBLE_ES = """<blockquote class="preamble">
<p>Alcohólicos Anónimos es una comunidad de personas que comparten su mutua experiencia, fortaleza y esperanza para resolver su problema común y ayudar a otros a recuperarse del alcoholismo.</p>
<p>El único requisito para ser miembro de A.A. es el deseo de dejar la bebida. Para ser miembro de A.A. no se pagan honorarios ni cuotas; nos mantenemos con nuestras propias contribuciones. A.A. no está afiliada a ninguna secta, religión, partido político, organización o institución alguna; no desea intervenir en controversias; no respalda ni se opone a ninguna causa. Nuestro objetivo primordial es mantenernos sobrios y ayudar a otros alcohólicos a alcanzar el estado de sobriedad.</p>
<footer>Preámbulo de A.A. © The AA Grapevine, Inc. Reimpreso con permiso.</footer>
</blockquote>"""

PREAMBLE_EN = """<blockquote class="preamble">
<p>Alcoholics Anonymous is a fellowship of people who share their experience, strength and hope with each other that they may solve their common problem and help others to recover from alcoholism.</p>
<p>The only requirement for membership is a desire to stop drinking. There are no dues or fees for A.A. membership; we are self-supporting through our own contributions. A.A. is not allied with any sect, denomination, politics, organization or institution; does not wish to engage in any controversy, neither endorses nor opposes any causes. Our primary purpose is to stay sober and help other alcoholics to achieve sobriety.</p>
<footer>A.A. Preamble © The AA Grapevine, Inc. Reprinted with permission.</footer>
</blockquote>"""

def first_meeting_es(n_es, n_en, n_en_sessions):
    return dict(
        LANG="es", OGLOCALE="es_CO", CANON=ES_PATH, HOME="../",
        LANGSW='<span lang="es">ES</span><a href="../en/first-meeting/" hreflang="en" lang="en">EN</a>',
        TITLE="¿Nuevo en A.A.? Reuniones de Alcohólicos Anónimos en Medellín",
        DESC="Qué es A.A., qué pasa en una reunión, reuniones abiertas y cerradas, anonimato y dónde hay grupos de Alcohólicos Anónimos en Medellín.",
        H1="¿Nuevo en A.A.?",
        LEAD="Si tiene problemas con la bebida, en A.A. hay personas que han pasado por lo mismo.",
        BODY=f"""
<h2>¿Qué es A.A.?</h2>
{PREAMBLE_ES}

<h2>¿Soy alcohólico?</h2>
<p>Solo usted puede responder esa pregunta. AA Colombia tiene un cuestionario de <a href="https://aacolombia.org/" target="_blank" rel="noopener">doce preguntas de autoevaluación</a>. En A.A. no se hacen diagnósticos.</p>

<h2>¿Qué pasa en una reunión?</h2>
<p>Se lee el Preámbulo. Los miembros comparten su experiencia: cómo bebían, cómo llegaron a A.A. y cómo viven hoy. Nadie interrumpe. La reunión cierra con la Oración de la Serenidad. Dura aproximadamente hora y media.</p>
<p>No tiene que hablar. Si se le pregunta, diga su nombre de pila. No tiene que decir que es alcohólico.</p>

<h2>¿Cuánto cuesta?</h2>
<p>Nada. En algunas reuniones se pasa una bolsa para los gastos del grupo. La contribución es voluntaria.</p>

<h2>¿Reunión abierta o cerrada?</h2>
<p>Las reuniones cerradas son solo para alcohólicos o para quienes creen tener un problema con la bebida. A las reuniones abiertas puede asistir cualquier persona.</p>

<h2>¿Quién se va a enterar?</h2>
<p>Nadie. En A.A. se usa el nombre de pila. No hay listas de asistencia ni registros. Lo que se dice en la reunión no sale de la reunión.</p>

<h2>¿A.A. es religioso?</h2>
<p>No. A.A. no está afiliada a ninguna religión. Hay miembros de todas las creencias y sin ninguna.</p>

<h2>¿Dónde hay reuniones?</h2>
<p>En Medellín, Bello, Envigado, Itagüí y Sabaneta hay {n_es} grupos registrados en AA Colombia. La mayoría se reúne todas las noches a las 7:00 p. m. Hay reuniones en línea y también {n_en_sessions} reuniones en inglés cada semana.</p>
<p><a class="cta" href="../">Ver los grupos en el mapa →</a></p>

<h2>Para familiares y amigos</h2>
<p>Al-Anon es para los familiares y amigos de alcohólicos. <a href="https://al-anon.org/es/" target="_blank" rel="noopener">al-anon.org/es</a></p>

<p class="note">Si al dejar de beber tiene temblores fuertes, convulsiones o alucinaciones, acuda a urgencias o llame al 123.</p>
""",
        NOTE='Sitio independiente, sin afiliación con Alcoholics Anonymous World Services ni AA Colombia. <a href="../">Mapa de reuniones</a> · <a href="https://aacolombia.org" target="_blank" rel="noopener">aacolombia.org</a>',
    )

def first_meeting_en(n_es, n_en, n_en_sessions):
    return dict(
        LANG="en", OGLOCALE="en_US", CANON=EN_PATH, HOME="../",
        LANGSW='<a href="../../primera-reunion/" hreflang="es" lang="es">ES</a><span lang="en">EN</span>',
        TITLE="New to A.A.? Alcoholics Anonymous meetings in Medellín",
        DESC="What A.A. is, what happens at a meeting, open and closed meetings, anonymity, and where the English-speaking A.A. meetings in Medellín are.",
        H1="New to A.A.?",
        LEAD="If you have a problem with drinking, there are people in A.A. who have been where you are.",
        BODY=f"""
<h2>What is A.A.?</h2>
{PREAMBLE_EN}

<h2>Am I an alcoholic?</h2>
<p>Only you can answer that. A.A. has <a href="https://www.aa.org/self-assessment" target="_blank" rel="noopener">twelve questions</a> that may help. A.A. does not make diagnoses.</p>

<h2>What happens at a meeting?</h2>
<p>The Preamble is read. Members share their experience: what it was like, what happened, and what it is like now. No one interrupts. The meeting closes with the Serenity Prayer. It lasts about an hour.</p>
<p>You do not have to speak. If asked, give your first name. You do not have to say you are an alcoholic.</p>

<h2>What does it cost?</h2>
<p>Nothing. At some meetings a basket is passed for the group's expenses. Contributions are voluntary.</p>

<h2>Open or closed meeting?</h2>
<p>Closed meetings are for alcoholics or anyone who may have a drinking problem. Open meetings are for anyone.</p>

<h2>Who will know?</h2>
<p>No one. First names only. There are no attendance records. What is said at the meeting stays at the meeting.</p>

<h2>Is A.A. religious?</h2>
<p>No. A.A. is not allied with any religion. Members hold every belief and none.</p>

<h2>Where are the meetings?</h2>
<p>There are {n_en_sessions} English-speaking meetings a week in El Poblado, Laureles, Belén and Sabaneta, and on Zoom. There are also {n_es} Spanish-speaking groups in the metropolitan area; most meet every evening at 7:00 p.m.</p>
<p><a class="cta" href="../">See the meetings on the map →</a></p>

<h2>If your Spanish is limited</h2>
<div class="card"><div class="phrase">
<b>Es mi primera reunión.</b><span>It's my first meeting.</span>
<b>Soy nuevo. / Soy nueva.</b><span>I'm new.</span>
<b>¿Es abierta o cerrada?</b><span>Is it open or closed?</span>
<b>Solo quiero escuchar.</b><span>I just want to listen.</span>
<b>No hablo mucho español.</b><span>I don't speak much Spanish.</span>
</div></div>

<h2>For family and friends</h2>
<p>Al-Anon is for the families and friends of alcoholics. <a href="https://al-anon.org" target="_blank" rel="noopener">al-anon.org</a></p>

<p class="note">If you have stopped drinking and have severe shaking, seizures or hallucinations, go to an emergency room or call 123.</p>
""",
        NOTE='Independent site, not affiliated with Alcoholics Anonymous World Services or AA Colombia. <a href="../">Meeting map</a> · <a href="https://aamedellin.org" target="_blank" rel="noopener">aamedellin.org</a>',
    )

def write_pages(d, analytics=""):
    tpl = open(os.path.join(ROOT, "page.html"), encoding="utf-8").read()
    es_list, en_list = d["es"], d["en"] + [m for m in d.get("manual", []) if not m.get("hidden") and m.get("lang") == "en"]
    import render as R
    n_en_sessions = len({(m["name"], s) for m in en_list for s in R.slots(m)})
    out_paths = []
    for P, path in ((first_meeting_es(len(es_list), len(en_list), n_en_sessions), ES_PATH),
                    (first_meeting_en(len(es_list), len(en_list), n_en_sessions), EN_PATH)):
        ld = {"@context": "https://schema.org", "@type": "Article", "headline": P["TITLE"], "description": P["DESC"],
              "inLanguage": P["LANG"], "url": SITE + path, "dateModified": d["updated"][:10],
              "author": {"@type": "Organization", "name": "AA Medellín Map", "url": SITE + "/"},
              "isPartOf": {"@type": "WebSite", "name": "AA Medellín Map", "url": SITE + "/"},
              "about": {"@type": "Thing", "name": "Alcoholics Anonymous meetings in Medellín"}}
        rep = dict(P, SITE=SITE, CANONICAL=SITE + path, ES_PATH=ES_PATH, EN_PATH=EN_PATH, ANALYTICS=analytics,
                   JSONLD=json.dumps(ld, ensure_ascii=False).replace("</", "<\\/"))
        rep["TITLE"], rep["DESC"] = esc(P["TITLE"]), esc(P["DESC"])
        out = tpl
        for k, v in rep.items():
            out = out.replace("{{%s}}" % k, str(v))
        left = re.findall(r"\{\{[A-Z_]+\}\}", out)
        assert not left, left
        fp = os.path.join(ROOT, path.strip("/"), "index.html")
        os.makedirs(os.path.dirname(fp), exist_ok=True)
        open(fp, "w", encoding="utf-8").write(out)
        out_paths.append(path)
    return out_paths
