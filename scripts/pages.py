"""Extra pages rendered from page.html: the newcomer's guide in Spanish (/primera-reunion/) and English (/en/first-meeting/)."""
import json, os, re, html

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://www.aamedellinmap.org"
esc = lambda s: html.escape(str(s), quote=True)

ES_PATH, EN_PATH = "/primera-reunion/", "/en/first-meeting/"

def first_meeting_es(n_es, n_en, n_en_sessions):
    return dict(
        LANG="es", OGLOCALE="es_CO", CANON=ES_PATH, HOME="../",
        LANGSW='<span lang="es">ES</span><a href="../en/first-meeting/" hreflang="en" lang="en">EN</a>',
        TITLE="Tu primera reunión de AA en Medellín: qué esperar y cómo llegar",
        DESC="Guía para quien va por primera vez a Alcohólicos Anónimos en Medellín: qué pasa en una reunión, qué es abierta o cerrada, cuánto cuesta, qué decir y dónde encontrar la reunión más cercana hoy.",
        H1="Tu primera reunión de AA en Medellín",
        LEAD="Si estás pensando en ir a una reunión de Alcohólicos Anónimos, esto es lo que puedes esperar. No hay que inscribirse, no cuesta nada y nadie te va a pedir explicaciones.",
        BODY=f"""
<h2>Lo esencial</h2>
<ul>
<li><b>Solo hace falta un requisito:</b> querer dejar de beber. No tienes que estar seguro de ser alcohólico ni haber tocado fondo.</li>
<li><b>Es gratis.</b> No hay inscripción, cuotas ni listas. En algunas reuniones pasan una bolsa para una contribución voluntaria (para el arriendo y el café); puedes no dar nada.</li>
<li><b>Es anónimo.</b> Se usa el nombre de pila. Nadie te pide documentos, nadie avisa a tu familia ni a tu trabajo.</li>
<li><b>Puedes solo escuchar.</b> No tienes que hablar ni presentarte. Si quieres, puedes decir «soy nuevo» y ya.</li>
<li><b>Llega unos minutos antes</b> y, si puedes, quédate un momento al final: ahí es donde la gente se acerca a saludar al que llega por primera vez.</li>
</ul>
<p><a class="cta" href="../">Ver las reuniones de hoy en el mapa →</a></p>

<h2>Qué pasa en una reunión</h2>
<p>Una reunión dura más o menos una hora y media. Normalmente alguien abre leyendo el preámbulo y los Doce Pasos, y después los miembros comparten por turnos su experiencia: cómo bebían, qué los trajo a AA y cómo viven hoy sin beber. Nadie interrumpe, nadie aconseja, nadie juzga. Al final se cierra con una oración breve (la Oración de la Serenidad); no hace falta ser creyente ni participar.</p>
<p>En Medellín hay {n_es} grupos en español y muchos se reúnen todas las noches, en general a las 7:00 pm; también hay reuniones al mediodía y en la mañana. Además hay {n_en_sessions} reuniones en inglés cada semana. Todas están en el mapa, con dirección, horario y cómo llegar.</p>

<h2>Reunión abierta y reunión cerrada</h2>
<p>Una <b>reunión cerrada</b> es solo para quienes tienen, o creen tener, un problema con el alcohol. Una <b>reunión abierta</b> la puede visitar cualquier persona: familiares, amigos, estudiantes, profesionales de la salud. Si vas por ti, puedes ir a cualquiera de las dos. Si acompañas a alguien o quieres conocer AA desde afuera, busca una abierta o pregunta en la puerta.</p>

<h2>¿Y si no quiero que me vean?</h2>
<p>Es normal. Puedes empezar con una reunión en línea o híbrida (están marcadas en el mapa; muchas usan Zoom y puedes dejar la cámara apagada) o ir a un grupo en un barrio distinto al tuyo. Nadie en AA te va a saludar en la calle a menos que tú lo hagas primero: la anonimidad también funciona hacia afuera.</p>

<div class="card">
<h2>Si tienes un familiar o amigo que bebe</h2>
<p>AA es para la persona que quiere dejar de beber; no se puede obligar a nadie. Para familiares y amigos existe <b>Al-Anon</b>, con grupos en Medellín y reuniones en línea (<a href="https://al-anon.org/es/" target="_blank" rel="noopener">al-anon.org/es</a>). Puedes acompañar a alguien a una reunión abierta de AA, pero lo que más ayuda suele ser cuidar de ti.</p>
</div>

<h2>Para quien no habla español</h2>
<p>Hay reuniones de AA en inglés en El Poblado, Laureles, Belén y Sabaneta, y por Zoom. Están en la <a href="../en/">versión en inglés de este sitio</a> con sus horarios. Muchos grupos en español reciben con gusto a visitantes extranjeros, pero la reunión se hace en español.</p>

<h2>Preguntas frecuentes de quien va por primera vez</h2>
<p><b>¿Tengo que decir que soy alcohólico?</b> No. Puedes presentarte solo con tu nombre, o no presentarte.</p>
<p><b>¿Puedo ir si estuve bebiendo hoy?</b> Sí, mientras no interrumpas la reunión. Más de uno llegó así a su primera reunión.</p>
<p><b>¿Hay que ir a un grupo en particular?</b> No. Puedes visitar varios hasta encontrar uno donde te sientas a gusto; cada grupo tiene su estilo.</p>
<p><b>¿Qué llevo?</b> Nada. Si quieres, algo de dinero suelto para la contribución voluntaria, y un cuaderno si eres de tomar notas.</p>
<p><b>¿Y si llego tarde?</b> Entra en silencio y siéntate. Nadie se molesta.</p>
<p><b>¿AA es religioso?</b> No. Habla de un «Poder Superior», pero cada quien lo entiende como quiera, y hay miembros ateos y agnósticos.</p>

<p class="note">Si estás en una emergencia médica (convulsiones, alucinaciones, temblores fuertes al dejar de beber), llama al 123 o ve a urgencias: la abstinencia alcohólica severa puede ser peligrosa y necesita atención médica. AA no reemplaza al médico, pero te acompaña después.</p>
""",
        NOTE='Sitio independiente, sin afiliación con Alcoholics Anonymous World Services ni AA Colombia. <a href="../">Mapa de reuniones</a> · <a href="https://aacolombia.org" target="_blank" rel="noopener">aacolombia.org</a>',
    )

def first_meeting_en(n_es, n_en, n_en_sessions):
    return dict(
        LANG="en", OGLOCALE="en_US", CANON=EN_PATH, HOME="../",
        LANGSW='<a href="../../primera-reunion/" hreflang="es" lang="es">ES</a><span lang="en">EN</span>',
        TITLE="Your first AA meeting in Medellín: what to expect, in English",
        DESC="A guide for newcomers and visitors going to Alcoholics Anonymous in Medellín, Colombia: English-speaking meetings, what happens in a meeting, open vs closed, cost, Spanish phrases, and how to find a meeting today.",
        H1="Your first AA meeting in Medellín",
        LEAD="If you're thinking about walking into a meeting, here is what to expect. No sign-up, no cost, and nobody will ask you to explain yourself.",
        BODY=f"""
<h2>The essentials</h2>
<ul>
<li><b>There is only one requirement:</b> a desire to stop drinking. You don't have to be sure you're an alcoholic, and you don't have to have hit bottom.</li>
<li><b>It's free.</b> No registration, no dues, no attendance lists. Some meetings pass a basket for a voluntary contribution (rent and coffee); you can let it pass.</li>
<li><b>It's anonymous.</b> First names only. Nobody asks for ID, nobody contacts your family or employer.</li>
<li><b>You can just listen.</b> You don't have to speak or introduce yourself. If you like, "I'm new" is plenty.</li>
<li><b>Arrive a few minutes early</b> and, if you can, stay a moment afterwards: that's when people come over to welcome a newcomer and swap numbers.</li>
</ul>
<p><a class="cta" href="../">See today's English meetings on the map →</a></p>

<h2>English-speaking meetings in Medellín</h2>
<p>There are {n_en_sessions} English-language meetings a week, in El Poblado, Laureles, Belén and Sabaneta, plus Zoom meetings you can join from anywhere. They're run by English-speaking expats and travelers and welcome visitors; you'll usually find people who have been sober a long time and others on their first week. The <a href="../">map</a> lists each one with its address, time and a contact.</p>
<p>If none fits your schedule, there are also {n_es} Spanish-speaking groups, most of them meeting every evening around 7:00 pm. Many are glad to have a foreign visitor even if your Spanish is basic (see the phrases below). Switch the map to "All" to see them.</p>

<h2>What happens in a meeting</h2>
<p>A meeting runs about an hour (Spanish groups often an hour and a half). Someone opens by reading the preamble and the Twelve Steps, then members take turns sharing their experience: what drinking was like, what brought them to AA, what life is like now. No cross-talk, no advice, no judgment. Meetings close with a short prayer (the Serenity Prayer); you don't need to be religious or join in.</p>

<h2>Open vs. closed meetings</h2>
<p>A <b>closed meeting</b> is for people who have, or think they may have, a drinking problem. An <b>open meeting</b> is for anyone: family, friends, students, health professionals. If you're coming for yourself, either one is fine. If you're accompanying someone, choose an open meeting or ask at the door.</p>

<h2>Worried about being seen?</h2>
<p>Common, and understandable in a city where the expat community is small. You can start with an online or hybrid meeting (marked on the map; camera off is fine), or pick a group across town. Nobody from AA will acknowledge you on the street unless you do first: anonymity works in both directions.</p>

<div class="card">
<h2>Useful Spanish at a meeting</h2>
<div class="phrase">
<b>Es mi primera reunión.</b><span>It's my first meeting.</span>
<b>Soy nuevo / nueva.</b><span>I'm new.</span>
<b>¿Esta reunión es abierta o cerrada?</b><span>Is this meeting open or closed?</span>
<b>Solo quiero escuchar.</b><span>I just want to listen.</span>
<b>No hablo mucho español.</b><span>I don't speak much Spanish.</span>
<b>¿A qué hora empieza?</b><span>What time does it start?</span>
<b>Gracias por recibirme.</b><span>Thank you for welcoming me.</span>
</div>
</div>

<h2>If someone you love drinks</h2>
<p>AA is for the person who wants to stop; nobody can be made to go. For family and friends there is <b>Al-Anon</b>, with meetings in Medellín and online in English (<a href="https://al-anon.org" target="_blank" rel="noopener">al-anon.org</a>). You can go with someone to an open AA meeting, but looking after yourself usually helps more than anything.</p>

<h2>Newcomer questions</h2>
<p><b>Do I have to say I'm an alcoholic?</b> No. Give your first name, or say nothing at all.</p>
<p><b>Can I come if I've been drinking today?</b> Yes, as long as you don't disrupt the meeting. Plenty of people arrived at their first meeting that way.</p>
<p><b>Do I have to pick a home group?</b> Not now. Try a few; each has its own feel.</p>
<p><b>What should I bring?</b> Nothing. Some coins or small bills if you'd like to contribute, and a notebook if you're the type.</p>
<p><b>What if I'm late?</b> Slip in quietly and sit down. Nobody minds.</p>
<p><b>Is AA religious?</b> No. It talks about a "Higher Power," which each member defines for themselves; there are atheists and agnostics in the rooms.</p>
<p><b>I'm only in Medellín for a week. Is it worth going?</b> Yes. Visitors are a normal part of the English-speaking meetings, and a meeting is the fastest way to meet sober people in a new city.</p>

<p class="note">If you're in a medical emergency (seizures, hallucinations, severe shaking after stopping drinking), call 123 or go to an emergency room: severe alcohol withdrawal can be dangerous and needs medical care. AA doesn't replace a doctor, but it's there afterwards.</p>
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
