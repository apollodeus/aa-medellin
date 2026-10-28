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
        TITLE="¿Nuevo en A.A.? Qué esperar en una reunión de Alcohólicos Anónimos en Medellín",
        DESC="Información para quien tiene un problema con la bebida y piensa asistir por primera vez a una reunión de Alcohólicos Anónimos en Medellín: qué es A.A., qué pasa en una reunión, reuniones abiertas y cerradas, y cómo encontrar un grupo hoy.",
        H1="¿Nuevo en A.A.?",
        LEAD="Si la bebida le está causando problemas, o si ha llegado al punto de preocuparle, es posible que le interese saber qué es Alcohólicos Anónimos y qué puede esperar en una reunión.",
        BODY=f"""
<h2>Solo usted puede decidir</h2>
<p>Nadie en A.A. va a decirle si es alcohólico. Eso lo decide cada uno. Si bebe más de lo que quisiera, si ha intentado dejarlo y no ha podido, o si la bebida le está trayendo problemas en la casa, en el trabajo o con la salud, puede que A.A. tenga algo que ofrecerle. El único requisito para ser miembro de A.A. es el deseo de dejar de beber. No hay que firmar nada, no se pagan honorarios ni cuotas y nadie le va a preguntar por qué vino.</p>
<p>Si tiene dudas, AA Colombia ofrece un <a href="https://aacolombia.org/" target="_blank" rel="noopener">cuestionario de autoevaluación de doce preguntas</a>. Es solo para usted.</p>

<h2>Qué es Alcohólicos Anónimos</h2>
<p>A.A. es una comunidad de hombres y mujeres que comparten su experiencia, fortaleza y esperanza para resolver su problema común y ayudar a otros a recuperarse del alcoholismo. Los miembros se reúnen en grupos. En Medellín y el área metropolitana hay {n_es} grupos registrados en AA Colombia; la mayoría se reúne todas las noches, por lo general a las 7:00 p. m., y algunos también al mediodía o en la mañana. A.A. no está afiliada a ninguna religión, partido político, institución ni organización, y se mantiene con las contribuciones voluntarias de sus propios miembros.</p>
<p><a class="cta" href="../">Encontrar un grupo en el mapa →</a></p>

<h2>Qué pasa en una reunión</h2>
<p>Las reuniones duran alrededor de hora y media. Al comienzo se leen el Preámbulo y, en muchos grupos, los Doce Pasos. Después los miembros comparten, por turnos y sin interrupciones, su experiencia con la bebida: cómo bebían, cómo llegaron a A.A. y cómo viven hoy sin beber. No se discute ni se aconseja. La reunión termina con una oración breve, generalmente la Oración de la Serenidad; nadie está obligado a participar en ella.</p>
<p>Usted no tiene que hablar. Puede escuchar y nada más. Si se le pregunta, basta con decir su nombre de pila y que es la primera vez que viene. Es costumbre que al final algunos miembros se acerquen a saludar al recién llegado y a ofrecerle su número de teléfono; es parte de cómo funciona A.A.</p>

<h2>Reuniones abiertas y cerradas</h2>
<p>Las <b>reuniones cerradas</b> son únicamente para alcohólicos o para quienes creen tener un problema con la bebida. Las <b>reuniones abiertas</b> admiten a cualquier persona interesada en A.A.: familiares, amigos, estudiantes, profesionales. Si usted viene por su propio problema con el alcohol, es bienvenido en las dos. Si viene a acompañar a alguien, pregunte en la puerta si la reunión es abierta.</p>

<h2>El anonimato</h2>
<p>El anonimato es la base espiritual de A.A. En las reuniones se usa el nombre de pila. No se llevan listas de asistencia ni historias clínicas, y lo que se dice en la reunión se queda en la reunión. Los miembros no revelan fuera de A.A. quién asiste. Si prefiere no ir a un grupo de su barrio, puede ir a otro, o empezar por una reunión virtual o híbrida: en el mapa aparecen marcadas.</p>

<h2>Lo que A.A. no hace</h2>
<p>A.A. no da diagnósticos médicos ni psicológicos, no ofrece tratamiento, desintoxicación, hospitalización ni medicamentos, no hace seguimiento a sus miembros ni intenta controlarlos, no ofrece servicios religiosos y no acepta dinero de fuentes ajenas a A.A. Si usted está en abstinencia y presenta temblores fuertes, convulsiones o alucinaciones, acuda a un servicio de urgencias o llame al 123: la abstinencia alcohólica grave requiere atención médica.</p>

<div class="card">
<h2>Para familiares y amigos</h2>
<p>A.A. es para el alcohólico que quiere dejar de beber. No se puede obligar a nadie. Los familiares y amigos de alcohólicos cuentan con <b>Al-Anon</b>, una comunidad distinta de A.A., con grupos en Medellín y reuniones en línea: <a href="https://al-anon.org/es/" target="_blank" rel="noopener">al-anon.org/es</a>.</p>
</div>

<h2>Reuniones en inglés</h2>
<p>En Medellín hay {n_en_sessions} reuniones de A.A. en inglés cada semana, en El Poblado, Laureles, Belén y Sabaneta, y por Zoom. Están en la <a href="../en/">versión en inglés de este sitio</a>.</p>

<p class="note">Este es un sitio independiente que reúne la información publicada por AA Colombia y por los grupos en inglés de Medellín. Para información oficial sobre A.A. consulte <a href="https://aacolombia.org" target="_blank" rel="noopener">aacolombia.org</a> y <a href="https://www.aa.org/es" target="_blank" rel="noopener">aa.org/es</a>.</p>
""",
        NOTE='Sitio independiente, sin afiliación con Alcoholics Anonymous World Services ni AA Colombia. <a href="../">Mapa de reuniones</a> · <a href="https://aacolombia.org" target="_blank" rel="noopener">aacolombia.org</a>',
    )

def first_meeting_en(n_es, n_en, n_en_sessions):
    return dict(
        LANG="en", OGLOCALE="en_US", CANON=EN_PATH, HOME="../",
        LANGSW='<a href="../../primera-reunion/" hreflang="es" lang="es">ES</a><span lang="en">EN</span>',
        TITLE="New to A.A.? What to expect at an A.A. meeting in Medellín",
        DESC="For anyone with a drinking problem who is thinking about going to an Alcoholics Anonymous meeting in Medellín, Colombia: what A.A. is, what happens at a meeting, open and closed meetings, English-speaking meetings, and how to find one today.",
        H1="New to A.A.?",
        LEAD="If you seem to be having trouble with your drinking, or if your drinking has reached the point where it worries you, you may want to know something about Alcoholics Anonymous and what to expect at a meeting.",
        BODY=f"""
<h2>Only you can decide</h2>
<p>No one in A.A. will tell you whether you are an alcoholic. That is for you to determine. If you drink more than you mean to, if you have tried to stop or cut down and could not, or if drinking is causing trouble at home, at work or with your health, A.A. may have something to offer you. The only requirement for A.A. membership is a desire to stop drinking. There is nothing to sign, there are no dues or fees, and no one will ask you why you came.</p>
<p>If you are not sure, A.A.'s pamphlet <a href="https://www.aa.org/self-assessment" target="_blank" rel="noopener">"Is A.A. for You?"</a> has twelve questions only you can answer.</p>

<h2>What A.A. is</h2>
<p>Alcoholics Anonymous is a fellowship of people who share their experience, strength and hope with each other that they may solve their common problem and help others to recover from alcoholism. Members meet in groups. A.A. is not allied with any sect, denomination, politics, organization or institution, and is self-supporting through its members' own contributions. Some meetings pass a basket; you are welcome to let it pass.</p>

<h2>Meetings in Medellín</h2>
<p>There are {n_en_sessions} English-speaking A.A. meetings a week in Medellín, in El Poblado, Laureles, Belén and Sabaneta, and on Zoom. They are run by English-speaking members who live here or pass through, and visitors are a normal part of them. Each one is on the <a href="../">map</a> with its address, time and a contact number.</p>
<p>There are also {n_es} Spanish-speaking groups registered with AA Colombia across the metropolitan area, most of them meeting every evening at 7:00 p.m. You are welcome at any of them; the meeting will be in Spanish, and a few words are enough to be understood (see below).</p>
<p><a class="cta" href="../">Find a meeting on the map →</a></p>

<h2>What happens at a meeting</h2>
<p>An English-speaking meeting here runs about an hour; Spanish-speaking groups usually an hour and a half. The meeting opens with the A.A. Preamble and often a reading from A.A. literature. Members then share, in turn and without interruption, their experience with alcohol: what it was like, what happened, and what it is like now. There is no cross-talk and no advice-giving. Meetings generally close with the Serenity Prayer; no one is required to take part.</p>
<p>You do not have to speak. You may simply listen. If you are asked, your first name and "it's my first meeting" is enough. It is customary for members to come over afterwards to welcome a newcomer and offer a phone number. That is how A.A. works.</p>

<h2>Open and closed meetings</h2>
<p><b>Closed meetings</b> are for A.A. members only, or for anyone who may have a drinking problem. <b>Open meetings</b> are for anyone interested in A.A., including family, friends, students and professionals. If you are coming because of your own drinking, you are welcome at both. If you are accompanying someone, choose an open meeting or ask at the door.</p>

<h2>Anonymity</h2>
<p>Anonymity is the spiritual foundation of A.A. First names only are used at meetings. A.A. keeps no attendance records or case histories, and what is said in the meeting stays in the meeting. Members do not disclose outside A.A. who attends. In a city where the English-speaking community is small this matters to many people; if you would rather not be seen at a particular group, there are others, and there are online and hybrid meetings, marked on the map.</p>

<h2>What A.A. does not do</h2>
<p>A.A. does not make medical or psychological diagnoses, provide detox, hospitalization, medication or treatment, follow up on or try to control its members, offer religious services, or accept money from outside sources. If you have stopped drinking and have severe shaking, seizures or hallucinations, go to an emergency room or call 123: severe alcohol withdrawal needs medical care.</p>

<div class="card">
<h2>A few words of Spanish for a meeting</h2>
<div class="phrase">
<b>Es mi primera reunión.</b><span>It's my first meeting.</span>
<b>Soy nuevo. / Soy nueva.</b><span>I'm new.</span>
<b>¿La reunión es abierta o cerrada?</b><span>Is the meeting open or closed?</span>
<b>Solo quiero escuchar.</b><span>I just want to listen.</span>
<b>No hablo mucho español.</b><span>I don't speak much Spanish.</span>
<b>Gracias por recibirme.</b><span>Thank you for having me.</span>
</div>
</div>

<h2>For family and friends</h2>
<p>A.A. is for the alcoholic who wants to stop drinking; no one can be made to go. Family and friends of alcoholics have <b>Al-Anon</b>, a separate fellowship, with meetings in Medellín and online in English: <a href="https://al-anon.org" target="_blank" rel="noopener">al-anon.org</a>.</p>

<p class="note">This is an independent site that gathers the information published by AA Colombia and by Medellín's English-speaking groups. For official information about A.A. see <a href="https://www.aa.org" target="_blank" rel="noopener">aa.org</a> and <a href="https://aamedellin.org" target="_blank" rel="noopener">aamedellin.org</a>.</p>
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
