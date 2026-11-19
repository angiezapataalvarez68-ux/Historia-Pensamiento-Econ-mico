"""
Historia del pensamiento económico — Taller con IA
Proyecto de Alexander Tobón Arias.
Paola Zapata.
App para el trabajo independiente del curso de Historia del Pensamiento Económico.
Tobón y Zapata (2026). Roles de Mollick y Mollick (2023); método de Marcuzzo (2008).

Ejecutar en local:   streamlit run app.py
"""
from __future__ import annotations

from datetime import datetime

import streamlit as st

from contenido import ESCUELAS, INTENCIONALIDADES, ROLES, construir_prompt
from corpus_rag import Buscador, formatear_contexto
from modelo import hay_clave, responder

st.set_page_config(page_title="Historia del pensamiento económico", page_icon="📜", layout="wide")

# ---------------------------------------------------------------------------
# Estilo
# ---------------------------------------------------------------------------
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
:root {
  --negro: #000000; --blanco: #FFFFFF; --gris-fondo: #F5F5F7; --tinta: #1D1D1F; --gris: #6E6E73; --gris-2: #86868B;
  --azul: #0071E3; --azul-link: #0066CC; --azul-oscuro: #2997FF; --linea: #D2D2D7;
  --sf: -apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", "Inter", "Helvetica Neue", "Segoe UI", sans-serif;
  --serif: "New York", "Iowan Old Style", "Palatino Linotype", Georgia, serif;
}
#MainMenu {visibility: hidden;} footer {visibility: hidden;}
header[data-testid="stHeader"] { background: transparent; height: 0; }
[data-testid="stToolbar"], [data-testid="stDecoration"] { display: none; }
[data-testid="stMain"], section.main { overflow-x: hidden; }
.stApp :is(h1,h2,h3,h4,h5,p,li,dt,dd,label,a,input,textarea,button,div,span):not([data-testid="stIconMaterial"]):not(.material-symbols-rounded) { font-family: var(--sf) !important; }
.stApp { background: var(--blanco); color: var(--tinta); -webkit-font-smoothing: antialiased; }
.stApp p, .stApp li { line-height: 1.47; letter-spacing: -0.022em; color: var(--tinta); }
.block-container { max-width: 1024px; padding-top: 0 !important; padding-bottom: 0; }
.ancho { width: 100vw; margin-left: calc(50% - 50vw); }

/* Barra de navegación local */
.navlocal { position: fixed; top: 0; left: 0; right: 0; z-index: 999991; height: 52px; display: flex; align-items: center; justify-content: space-between;
  padding: 0 max(22px, calc(50vw - 490px)); background: rgba(251,251,253,.78); backdrop-filter: saturate(180%) blur(20px); -webkit-backdrop-filter: saturate(180%) blur(20px);
  border-bottom: 1px solid rgba(0,0,0,.08); }
.navlocal .marca { font-size: 19px; font-weight: 600; letter-spacing: -0.02em; color: var(--tinta); }
.navlocal nav { display: flex; align-items: center; gap: 22px; }
.navlocal nav a { font-size: 12.5px; color: var(--tinta) !important; text-decoration: none; opacity: .85; }
.navlocal nav a:hover { opacity: 1; color: var(--azul-link) !important; }
.navlocal nav a.pildora { background: var(--azul); color: #fff !important; padding: 5px 12px; border-radius: 980px; opacity: 1; font-weight: 500; }

/* Portada */
.heroa { background: #FBFBFD; color: var(--tinta); text-align: center; padding: 150px 22px 80px; }
.heroa .nuevo { font-size: 17px; font-weight: 600; color: var(--gris); letter-spacing: -0.01em; margin-bottom: 14px; }
.heroa h1 { font-size: clamp(44px, 7.4vw, 88px) !important; line-height: 1.05 !important; font-weight: 700 !important; letter-spacing: -0.035em !important; color: var(--tinta) !important; margin: 0 auto !important; max-width: 980px; padding: 0 !important; }
.grad { color: var(--gris-2) !important; }
.heroa .sub { font-size: clamp(19px, 2.2vw, 24px) !important; color: var(--gris) !important; max-width: 700px; margin: 26px auto 0 !important; line-height: 1.35 !important; font-weight: 500; letter-spacing: -0.015em; }
.heroa .acciones { margin-top: 34px; display: flex; gap: 26px; justify-content: center; align-items: center; flex-wrap: wrap; }
.btn-azul { background: var(--azul); color: #fff !important; text-decoration: none !important; font-size: 17px; padding: 12px 24px; border-radius: 980px; font-weight: 500; }
.btn-azul:hover { background: #0077ED; }
.link-azul { color: var(--azul-link) !important; text-decoration: none !important; font-size: 17px; }
.link-azul:hover { text-decoration: underline !important; }
.heroa .autores { margin-top: 64px; font-size: 14px; color: var(--gris-2); line-height: 1.6; }
.heroa .autores b { color: var(--tinta); font-weight: 600; display: block; font-size: 17px; }
.demo.demo-claro { color: var(--gris) !important; border-color: var(--linea) !important; margin: 0 0 18px; }
.demo { display: inline-block; margin-top: 18px; font-size: 12px; color: var(--gris); border: 1px solid var(--linea); border-radius: 980px; padding: 4px 12px; }

/* Cronología */
.crono { background: #FBFBFD; padding: 36px 0 40px; overflow: hidden; border-top: 1px solid var(--linea); border-bottom: 1px solid var(--linea); }
.crono-fila { display: flex; justify-content: center; gap: clamp(18px, 3.4vw, 46px); flex-wrap: nowrap; }
.crono-fila div { text-align: center; }
.crono-fila b { display: block; font-size: clamp(26px, 3.6vw, 44px); font-weight: 600; letter-spacing: -0.03em; color: var(--tinta); line-height: 1; }
.crono-fila span { display: block; font-size: 12px; color: var(--gris-2); margin-top: 10px; letter-spacing: 0; }
.crono-fila div:nth-child(odd) b { color: var(--gris-2); }

/* Secciones */
.seccion { padding: 110px 0 36px; text-align: center; scroll-margin-top: 60px; }
.seccion .eti { font-size: 17px; font-weight: 600; color: var(--gris); margin-bottom: 8px; }
.seccion h2 { font-size: clamp(36px, 5.2vw, 56px) !important; font-weight: 700 !important; letter-spacing: -0.03em !important; line-height: 1.07 !important; color: var(--tinta) !important; margin: 0 !important; padding: 0 !important; }
.seccion p { font-size: 21px !important; color: var(--gris) !important; max-width: 640px; margin: 18px auto 0 !important; line-height: 1.38 !important; }

/* Mosaico de escuelas */
[data-testid="stVerticalBlock"]:has(> [data-testid="stElementContainer"] .tile-esc) {
  background: var(--gris-fondo); border-radius: 28px; padding: 34px 30px 22px; min-height: 330px; transition: transform .25s ease, box-shadow .25s ease;
}
[data-testid="stVerticalBlock"]:has(> [data-testid="stElementContainer"] .tile-esc):hover { transform: scale(1.012); box-shadow: 0 8px 30px rgba(0,0,0,.08); }
[data-testid="stVerticalBlock"]:has(> [data-testid="stElementContainer"] .tile-sel) { box-shadow: 0 0 0 2px var(--azul) !important; background: #FFFFFF; }
.tile-anio { font-size: 64px; font-weight: 700; letter-spacing: -0.045em; line-height: 1; }
.tile-nombre { font-size: 26px; font-weight: 600; letter-spacing: -0.02em; color: var(--tinta); margin-top: 22px; line-height: 1.15; }
.tile-periodo { font-size: 12px; font-weight: 600; color: var(--gris); text-transform: uppercase; letter-spacing: .04em; margin-top: 6px; }
.tile-lema { font-size: 17px; color: var(--gris); line-height: 1.42; margin-top: 12px; min-height: 4.4em; letter-spacing: -0.02em; }

/* Papeles de la IA */
.franja-negra { background: var(--negro); padding: 6px 0 40px; }
[data-testid="stVerticalBlock"]:has(> [data-testid="stElementContainer"] .tile-rol) {
  background: var(--gris-fondo); border-radius: 28px; padding: 36px 30px 24px; min-height: 340px; transition: transform .25s ease;
}
[data-testid="stVerticalBlock"]:has(> [data-testid="stElementContainer"] .tile-rol):hover { transform: scale(1.012); }
[data-testid="stVerticalBlock"]:has(> [data-testid="stElementContainer"] .rol-sel) { box-shadow: 0 0 0 2px var(--azul) !important; background: #FFFFFF; }
.rol-eti { font-size: 14px; font-weight: 600; color: var(--gris); }
.rol-nombre { font-size: clamp(28px, 3.1vw, 40px); white-space: nowrap; font-weight: 700; letter-spacing: -0.035em; line-height: 1.05; margin-top: 6px; }
.rol-texto { font-size: 17px; color: var(--gris) !important; line-height: 1.45; margin-top: 16px; min-height: 6em; letter-spacing: -0.02em; }
.rol-meta { font-size: 12px; color: var(--gris-2); margin: 14px 0 4px; }
.seccion-oscura { background: var(--negro); }
.seccion-oscura h2 { color: #F5F5F7 !important; }
.seccion-oscura p { color: var(--gris-2) !important; }
.seccion-oscura .eti { color: var(--gris-2); }

/* Cifras */
.cifras { display: flex; justify-content: center; gap: clamp(20px, 5vw, 70px); padding: 30px 0 20px; flex-wrap: wrap; }
.cifras > div { text-align: center; width: 230px; }
.cifras b { display: block; font-size: clamp(56px, 8vw, 96px); font-weight: 700; letter-spacing: -0.05em; line-height: 1; }
.cifras .lbl { display: block; font-size: 17px; color: var(--gris); margin-top: 10px; max-width: 220px; line-height: 1.35; }

/* Comenzar */
[data-testid="stVerticalBlock"]:has(> [data-testid="stElementContainer"] .tile-inicio) {
  background: var(--gris-fondo); border-radius: 28px; padding: 54px 40px 40px; text-align: center;
}
.res-eti { font-size: 17px; font-weight: 600; color: var(--gris); }
.res-txt { font-size: clamp(28px, 3.6vw, 40px); font-weight: 700; letter-spacing: -0.03em; line-height: 1.1; color: var(--tinta); margin: 8px 0 26px; }
.res-txt em { font-style: normal; color: var(--gris); font-weight: 600; }
.res-vacio { color: #AEAEB2 !important; }
.aviso { font-size: 12px; color: var(--gris); line-height: 1.5; max-width: 700px; margin: 22px auto 0; text-align: center; }

/* Botones de Streamlit */
.stButton button, .stDownloadButton button {
  white-space: nowrap !important; width: auto !important; border-radius: 980px !important; font-weight: 500 !important; font-size: 15px !important; padding: 8px 18px !important; min-height: 0 !important;
  border: none !important; background: transparent !important; color: var(--azul-link) !important; box-shadow: none !important;
}
.stButton button p, .stDownloadButton button p { color: inherit !important; font-size: 17px !important; white-space: nowrap !important; }
.stButton button > div { flex-direction: row !important; gap: 6px; }
.stButton button:hover, .stDownloadButton button:hover { text-decoration: underline; color: var(--azul-link) !important; }
.stButton button[kind="primary"] { background: var(--azul) !important; color: #FFF !important; }
.stButton button[kind="primary"] p { color: #FFF !important; }
.stButton button[kind="primary"]:hover { background: #0077ED !important; text-decoration: none; }
.stButton button:disabled { background: #E8E8ED !important; }
.stButton button:disabled p { color: #AEAEB2 !important; }
[data-testid="stVerticalBlock"]:has(> [data-testid="stElementContainer"] .tile-esc) .stButton, [data-testid="stVerticalBlock"]:has(> [data-testid="stElementContainer"] .tile-rol) .stButton { margin-left: -18px; }

.st-key-comenzar { display: flex; justify-content: center; }
.st-key-comenzar button { padding: 14px 34px !important; }
.st-key-comenzar button p { font-size: 19px !important; }

/* Pie */
.pie { background: var(--gris-fondo); padding: 30px 0 40px; margin-top: 90px; }
.pie-in { max-width: 980px; margin: 0 auto; padding: 0 22px; font-size: 12px; color: var(--gris); line-height: 1.6; }
.pie-in .linea { border-top: 1px solid var(--linea); margin: 14px 0; }
.pie-in b { color: var(--tinta); font-weight: 600; }
[data-testid="stExpander"] { border: none !important; }
[data-testid="stExpander"] details { border: none !important; border-top: 1px solid var(--linea) !important; border-radius: 0 !important; }
[data-testid="stExpander"] summary p { font-size: 15px; color: var(--azul-link) !important; }

/* Sesión */
.cab-sesion { padding: 70px 0 18px; border-bottom: 1px solid var(--linea); margin-bottom: 26px; }
.cab-sesion .eti { font-size: 17px; font-weight: 600; color: var(--gris); }
.cab-sesion h2 { font-size: clamp(36px, 5vw, 52px) !important; font-weight: 700 !important; letter-spacing: -0.035em !important; line-height: 1.07 !important; margin: 4px 0 0 !important; padding: 0 !important; color: var(--tinta) !important; }
[data-testid="stChatMessage"] { background: transparent; padding: 0; margin-bottom: 18px; gap: 0; }
[data-testid="stChatMessage"] > div[aria-hidden="true"], [data-testid="stChatMessage"] [data-testid*="Avatar"], [data-testid="stChatMessageAvatarUser"], [data-testid="stChatMessageAvatarAssistant"], [data-testid="stChatMessageAvatarCustom"] { display: none !important; }
[data-testid="stChatMessage"] [data-testid="stChatMessageContent"] { background: var(--gris-fondo); border-radius: 22px; padding: 16px 22px; max-width: 88%; }
[data-testid="stChatMessage"]:has(.msg-user) { flex-direction: row-reverse; }
[data-testid="stChatMessage"]:has(.msg-user) [data-testid="stChatMessageContent"] { background: var(--azul); border-bottom-right-radius: 6px; max-width: 72%; margin-left: auto; }
[data-testid="stChatMessage"]:has(.msg-user) p { color: #FFFFFF !important; font-size: 17px; }
[data-testid="stChatMessage"]:not(:has(.msg-user)) [data-testid="stChatMessageContent"] { border-bottom-left-radius: 6px; }
[data-testid="stChatMessage"] p { font-size: 17px; line-height: 1.5; }
[data-testid="stElementContainer"]:has(.msg-user), .msg-user { display: none; }
.stApp blockquote { border-left: 3px solid #1D1D1F !important; background: #FFFFFF !important; border-radius: 0 14px 14px 0; padding: 14px 20px !important; margin: 14px 0 !important; opacity: 1 !important; }
html body .stApp blockquote :is(p,span,em,strong):not([data-testid="stIconMaterial"]):not(.material-symbols-rounded):not(.x-serif) { font-family: var(--serif) !important; font-size: 18px; line-height: 1.55; color: #1D1D1F !important; font-style: italic; }
[data-testid="stBottom"] > div { background: rgba(255,255,255,.9); }
[data-testid="stChatInput"] { border-radius: 980px !important; border: 1px solid var(--linea) !important; background: #FFFFFF !important; }
[data-testid="stChatInput"]:focus-within { border-color: var(--azul) !important; box-shadow: 0 0 0 4px rgba(0,113,227,.15); }
[data-testid="stChatInputSubmitButton"] { background: var(--azul) !important; border-radius: 50% !important; color: #FFF !important; }
[data-testid="stSidebar"] { background: var(--gris-fondo); border-right: 1px solid var(--linea); }
[data-testid="stSidebar"] .eyebrow { font-size: 12px; font-weight: 600; color: var(--gris); text-transform: none; }
[data-testid="stSidebar"] h3 { font-size: 28px !important; font-weight: 700 !important; letter-spacing: -0.03em; line-height: 1.1; color: var(--tinta) !important; }
[data-testid="stSidebar"] h4 { font-size: 12px !important; font-weight: 600 !important; color: var(--gris) !important; text-transform: uppercase; letter-spacing: .04em; margin-top: 22px; }
.chip { display: inline-block; padding: 4px 12px; border-radius: 980px; background: #FFFFFF; border: 1px solid var(--linea); font-size: 12px; margin: 0 6px 6px 0; color: var(--tinta); }
.ficha dt { font-size: 12px; font-weight: 600; color: var(--tinta); margin-top: 14px; }
.ficha dd { margin: 2px 0 0 0; font-size: 14px; color: var(--gris); line-height: 1.5; }
[data-testid="stProgress"] > div > div > div > div { background: var(--azul) !important; }
[data-testid="stSidebar"] .stButton button, [data-testid="stSidebar"] .stDownloadButton button { padding-left: 0 !important; }
.credito { margin-top: 24px; font-size: 12px; color: var(--gris); line-height: 1.5; }
.credito .autor { color: var(--tinta); font-weight: 600; }
@media (max-width: 760px) { .navlocal nav a:not(.pildora) { display: none; } .heroa { padding-top: 120px; } .crono-fila span { display: none; } }
</style>
""",
    unsafe_allow_html=True,
)

AVISO_PRIVACIDAD = (
    "🔒 No escribas datos personales (nombre, documento, correo). "
    "Las conversaciones se procesan con el nivel gratuito de Gemini, que puede usar el contenido para mejorar sus productos. "
    "La IA puede equivocarse: verifica todo con las lecturas del curso."
)

# ---------------------------------------------------------------------------
# Estado
# ---------------------------------------------------------------------------
ss = st.session_state
ss.setdefault("escuela", None)
ss.setdefault("rol", None)
ss.setdefault("en_sesion", False)
ss.setdefault("mensajes", [])
ss.setdefault("inicio", None)


@st.cache_resource(show_spinner=False)
def buscador(escuela_id: str) -> Buscador:
    return Buscador(escuela_id)


def iniciar_sesion():
    ss.en_sesion = True
    ss.mensajes = []
    ss.inicio = datetime.now()


def terminar_sesion():
    ss.en_sesion = False
    ss.mensajes = []


def intercambios() -> int:
    return sum(1 for m in ss.mensajes if m["role"] == "user")


def transcripcion() -> str:
    e, r = ESCUELAS[ss.escuela], ROLES[ss.rol]
    lineas = [
        "# Historia del pensamiento económico — registro de la sesión",
        "Taller con IA · Alexander Tobón Arias  ",
        "Paola Zapata  ",
        f"Escuela: {e['nombre']}  ",
        f"Rol de la IA: {r['nombre']}  ",
        f"Fecha: {ss.inicio:%Y-%m-%d %H:%M}",
        "",
    ]
    for m in ss.mensajes:
        quien = "Estudiante" if m["role"] == "user" else f"IA ({r['nombre']})"
        lineas += [f"## {quien}", m["content"], ""]
    lineas += [
        "---",
        "Reflexión (completa antes de entregar): ¿Qué aprendiste? ¿Qué verificaste en las lecturas? "
        "¿En qué se equivocó la IA o qué no supo responder?",
    ]
    return "\n".join(lineas)


def ficha_html(escuela_id: str) -> str:
    e = ESCUELAS[escuela_id]
    alt = e["alternativa"] or "Es la base de la teoría económica dominante: se estudia qué conserva la teoría actual y qué se perdió."
    filas = [
        ("Problema central", e["problema"]),
        ("Núcleo en lenguaje actual", e["nucleo"]),
        ("Alternativa frente a la teoría dominante", alt),
        ("Visión e ideología", e["vision"]),
    ]
    cuerpo = "".join(f"<dt>{t}</dt><dd>{v[0].upper() + v[1:]}.</dd>" for t, v in filas)
    return f"<dl class='ficha'>{cuerpo}</dl>"


# ---------------------------------------------------------------------------
# Pantalla 1: elegir escuela y rol
# ---------------------------------------------------------------------------
AUTORES = ["Alexander Tobón Arias", "Paola Zapata"]
ANIOS = {"mercantilismo": "1664", "fisiocracia": "1758", "clasica": "1776",
         "neoclasica": "1871", "marxista": "1867", "keynesiana": "1936"}
GRADIENTES = {
    "mercantilismo": "linear-gradient(135deg,#FF9F0A,#FF375F)",
    "fisiocracia": "linear-gradient(135deg,#30D158,#00C7BE)",
    "clasica": "linear-gradient(135deg,#0A84FF,#5E5CE6)",
    "neoclasica": "linear-gradient(135deg,#64D2FF,#0A84FF)",
    "marxista": "linear-gradient(135deg,#FF453A,#BF5AF2)",
    "keynesiana": "linear-gradient(135deg,#BF5AF2,#5E5CE6)",
}
GRAD_ROL = {"tutor": "linear-gradient(90deg,#2997FF,#64D2FF)",
            "estudiante": "linear-gradient(90deg,#FF9F0A,#FF375F)",
            "simulador": "linear-gradient(90deg,#BF5AF2,#FF375F)"}


def autores_html(clase_autor: str = "autor") -> str:
    return "".join(f"<div class='{clase_autor}'>{a}</div>" for a in AUTORES)


@st.cache_data(show_spinner=False)
def cifras_corpus() -> tuple[int, int]:
    import pathlib, re as _re
    archivos = {p.name: p for e in ESCUELAS for p in (pathlib.Path("corpus") / e).glob("*.md")}  # solo obras, sin repetidos
    titulos = [p.read_text(encoding="utf-8").split("\n", 1)[0] for p in archivos.values()]
    autores = set()
    for t in titulos:
        nombre = t.lstrip("# ").split(",")[0]
        for a in _re.split(r"\s+y\s+", nombre):
            autores.add(a.strip())
    return len(titulos), len(autores)


def gtxt(texto: str, gradiente: str = "") -> str:
    """Diseño sobrio: cifras y títulos en tinta, sin degradados."""
    return f"<span style='color:#1D1D1F'>{texto}</span>"


def pantalla_inicio():
    n_textos, n_autores = cifras_corpus()
    demo = "" if hay_clave() else "<div><span class='demo'>Modo demostración · respuestas de ejemplo</span></div>"
    st.markdown(
        f"""
<div class="navlocal"><div class="marca">Historia del pensamiento económico</div>
  <nav><a href="#escuelas">Escuelas</a><a href="#papeles">La IA</a><a href="#fuentes">Fuentes</a><a class="pildora" href="#comenzar">Comenzar</a></nav></div>
<section class="ancho heroa">
  <div class="nuevo">Taller con inteligencia artificial</div>
  <h1>Pensar la economía<br><span class="grad">con quienes la inventaron.</span></h1>
  <p class="sub">Seis escuelas. Tres maneras de conversar con la IA. Y {n_textos} textos originales para comprobar cada idea en su fuente.</p>
  <div class="acciones"><a class="btn-azul" href="#comenzar">Empezar una sesión</a><a class="link-azul" href="#fuentes">Ver las fuentes ›</a></div>
  <div class="autores">Un proyecto de<b>{AUTORES[0]}</b><b>{AUTORES[1]}</b></div>
  {demo}
</section>
<section class="ancho crono"><div class="crono-fila">
  <div><b>1664</b><span>Mun</span></div><div><b>1758</b><span>Quesnay</span></div><div><b>1776</b><span>Smith</span></div>
  <div><b>1817</b><span>Ricardo</span></div><div><b>1867</b><span>Marx</span></div><div><b>1890</b><span>Marshall</span></div><div><b>1936</b><span>Keynes</span></div>
</div></section>
<div class="seccion" id="escuelas"><div class="eti">Escuelas</div><h2>Cinco siglos de ideas.<br>Elige por dónde empezar.</h2>
<p>Cada escuela parte de un problema distinto. Reconstrúyela desde ese problema, con sus propias palabras.</p></div>
""",
        unsafe_allow_html=True,
    )
    items = list(ESCUELAS.items())
    for fila in range(0, len(items), 3):
        cols = st.columns(3, gap="medium")
        for col, (eid, e) in zip(cols, items[fila:fila + 3]):
            elegida = ss.escuela == eid
            with col.container():
                st.markdown(
                    f"<div class='tile-esc {'tile-sel' if elegida else ''}'></div>"
                    f"<div class='tile-anio'>{gtxt(ANIOS.get(eid, ''), GRADIENTES.get(eid, ''))}</div>"
                    f"<div class='tile-nombre'>{e['nombre']}</div><div class='tile-periodo'>{e['periodo']}</div>"
                    f"<div class='tile-lema'>{e['lema']}</div>",
                    unsafe_allow_html=True,
                )
                if st.button("✓ Elegida" if elegida else "Elegir ›", key=f"esc_{eid}", type="primary" if elegida else "secondary"):
                    ss.escuela = eid
                    st.rerun()

    st.markdown(
        "<div class='seccion' id='papeles'>"
        "<div class='eti'>La IA</div><h2>Tres maneras de conversar.</h2>"
        "<p>La IA no te hace la tarea: te pregunta, se equivoca a propósito o te pone a decidir en la historia.</p></div>",
        unsafe_allow_html=True,
    )
    cols = st.columns(len(ROLES), gap="medium")
    for col, (rid, r) in zip(cols, ROLES.items()):
        elegido = ss.rol == rid
        with col.container():
            st.markdown(
                f"<div class='tile-rol {'rol-sel' if elegido else ''}'></div>"
                f"<div class='rol-eti'>La IA como</div>"
                f"<div class='rol-nombre'>{gtxt(r['nombre'] + '.', GRAD_ROL.get(rid, GRAD_ROL['tutor']))}</div>"
                f"<div class='rol-texto'>{r['resumen']}</div>"
                f"<div class='rol-meta'>Hasta {r['max_intercambios']} intercambios</div>",
                unsafe_allow_html=True,
            )
            if st.button("✓ Elegido" if elegido else "Elegir ›", key=f"rol_{rid}", type="primary" if elegido else "secondary"):
                ss.rol = rid
                st.rerun()

    st.markdown(
        f"""
<div class="seccion" id="fuentes"><div class="eti">Fuentes</div><h2>Cada idea, en su texto original.</h2>
<p>La IA cita pasajes de las obras en su edición original o en traducciones históricas, y los traduce para ti.</p></div>
<div class="cifras">
  <div><b>{gtxt(str(n_textos), 'linear-gradient(135deg,#FF9F0A,#FF375F)')}</b><span class='lbl'>textos originales en dominio público</span></div>
  <div><b>{gtxt(str(n_autores), 'linear-gradient(135deg,#0A84FF,#BF5AF2)')}</b><span class='lbl'>autores, de Mun a Hobson</span></div>
  <div><b>{gtxt(str(len(ESCUELAS) * len(ROLES)), 'linear-gradient(135deg,#30D158,#0A84FF)')}</b><span class='lbl'>combinaciones de escuela y papel de la IA</span></div>
</div>
<div class="seccion" id="comenzar" style="padding-top:90px"><div class="eti">Comenzar</div><h2>Tu sesión, en un clic.</h2></div>
""",
        unsafe_allow_html=True,
    )
    listo = ss.escuela and ss.rol
    with st.container():
        if listo:
            resumen = (f"<div class='res-txt'>{ESCUELAS[ss.escuela]['nombre']}<br>"
                       f"<em>con la IA como {ROLES[ss.rol]['nombre'].lower()}.</em></div>")
        else:
            resumen = "<div class='res-txt res-vacio'>Elige una escuela<br>y un papel para la IA.</div>"
        st.markdown(f"<div class='tile-inicio'></div><div class='res-eti'>Tu sesión</div>{resumen}", unsafe_allow_html=True)
        if st.button("Comenzar la sesión", type="primary", disabled=not listo, key="comenzar"):
            iniciar_sesion()
            st.rerun()
        st.markdown(f"<div class='aviso'>{AVISO_PRIVACIDAD}</div>", unsafe_allow_html=True)

    with st.expander("Las tres intencionalidades formativas del curso"):
        for k, v in INTENCIONALIDADES.items():
            st.markdown(f"**{k.capitalize()}.** {v}")

    st.markdown(
        f"""<div class="ancho pie"><div class="pie-in">
Las respuestas de la IA pueden equivocarse: verifica cada cita en la obra original. Los textos del corpus están en dominio público.
<div class="linea"></div>
<b>Historia del pensamiento económico · Taller con IA</b><br>Un proyecto de {AUTORES[0]}<br>{AUTORES[1]}
<div class="linea"></div>Roles de Mollick y Mollick (2023) · Método de Marcuzzo (2008)</div></div>""",
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Pantalla 2: sesión de chat
# ---------------------------------------------------------------------------
def pantalla_sesion():
    e, r = ESCUELAS[ss.escuela], ROLES[ss.rol]
    maximo = r["max_intercambios"]
    busc = buscador(ss.escuela)

    # Barra lateral
    with st.sidebar:
        st.markdown(f"<div class='eyebrow'>Sesión en curso</div>", unsafe_allow_html=True)
        st.markdown(f"### {e['nombre']}")
        st.markdown(f"<span class='chip'>{r['icono']} {r['nombre']}</span><span class='chip'>{e['periodo']}</span>",
                    unsafe_allow_html=True)
        n = intercambios()
        st.progress(min(n / maximo, 1.0), text=f"Intercambio {n} de {maximo}")
        st.markdown("#### Ficha de la escuela")
        st.markdown(ficha_html(ss.escuela), unsafe_allow_html=True)
        with st.expander(f"Fuentes del corpus ({len(busc.fuentes)})"):
            for f in busc.fuentes:
                st.markdown(f"- {f}")
        st.divider()
        st.download_button("⬇️ Descargar conversación", transcripcion(),
                           file_name=f"sesion_{ss.escuela}_{ss.rol}.md", mime="text/markdown",
                           use_container_width=True, disabled=not ss.mensajes)
        st.caption("Entrega este registro con tu reflexión, como piden Mollick y Mollick (2023).")
        if st.button("↺ Nueva sesión", use_container_width=True):
            terminar_sesion()
            st.rerun()
        st.markdown(f"<div class='aviso'>{AVISO_PRIVACIDAD}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='credito'>Historia del pensamiento económico{autores_html()}</div>",
                    unsafe_allow_html=True)

    # Cabecera
    st.markdown(
        f"<div class='cab-sesion'><div class='eti'>La IA como {r['nombre'].lower()} · {e['periodo']}</div>"
        f"<h2>{e['nombre']}</h2></div>",
        unsafe_allow_html=True,
    )
    if not hay_clave():
        st.markdown("<span class='demo demo-claro'>Modo demostración · respuestas de ejemplo</span>", unsafe_allow_html=True)

    prompt_sistema = construir_prompt(ss.escuela, ss.rol)

    # La IA abre la conversación
    if not ss.mensajes:
        with st.spinner("Preparando la sesión…"):
            texto = responder(prompt_sistema, formatear_contexto(busc.buscar(e["nucleo"])), [])
        ss.mensajes.append({"role": "assistant", "content": texto})

    for m in ss.mensajes:
        with st.chat_message(m["role"], avatar=r["icono"] if m["role"] == "assistant" else "🧑‍🎓"):
            if m["role"] == "user":
                st.markdown("<span class='msg-user'></span>", unsafe_allow_html=True)
            st.markdown(m["content"])

    if intercambios() >= maximo:
        st.success("Terminaste la sesión. Descarga la conversación desde la barra lateral y escribe tu reflexión.", icon="✅")
        return

    if entrada := st.chat_input("Escribe tu respuesta…"):
        ss.mensajes.append({"role": "user", "content": entrada})
        with st.chat_message("user", avatar="🧑‍🎓"):
            st.markdown(entrada)
        with st.chat_message("assistant", avatar=r["icono"]):
            with st.spinner("Pensando…"):
                consulta = " ".join(m["content"] for m in ss.mensajes[-3:])
                texto = responder(prompt_sistema, formatear_contexto(busc.buscar(consulta)), ss.mensajes)
            st.markdown(texto)
        ss.mensajes.append({"role": "assistant", "content": texto})
        st.rerun()


# ---------------------------------------------------------------------------
if ss.en_sesion and ss.escuela and ss.rol:
    pantalla_sesion()
else:
    pantalla_inicio()
