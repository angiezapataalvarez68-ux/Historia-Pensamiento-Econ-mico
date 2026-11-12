"""
Historia del pensamiento económico — Taller con IA
Proyecto de Alexander Tobón Arias.
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
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,500;0,600;1,500;1,600&family=Inter:wght@400;500;600&display=swap');
:root {
  --fondo: #FAF9F6; --tarjeta: #FFFFFF; --lateral: #F2F2EE; --linea: #E2E2DC;
  --oliva: #3D4F3D; --salvia: #556B52; --cita-fondo: #F0F3EF; --oliva-claro: #E6EBE4;
  --tinta: #1D1D1F; --gris: #6E6E73;
  --sombra: 0 4px 20px rgba(0, 0, 0, 0.03);
  --sans: -apple-system, BlinkMacSystemFont, "SF Pro Display", "Inter", "Segoe UI", sans-serif;
  --serif: "Cormorant Garamond", "Georgia", serif;
}

/* Limpieza */
#MainMenu {visibility: hidden;} footer {visibility: hidden;}
header[data-testid="stHeader"] { background: transparent; }
[data-testid="stToolbar"], [data-testid="stDecoration"] { display: none; }

/* Base */
.stApp :is(h1,h2,h3,h4,h5,p,li,dt,dd,label,a,input,textarea,button,div,span):not([data-testid="stIconMaterial"]):not(.material-symbols-rounded) { font-family: var(--sans) !important; }
.stApp { background: var(--fondo); color: var(--tinta); -webkit-font-smoothing: antialiased; }
.stApp p, .stApp li { line-height: 1.65; color: var(--tinta); }
h1, h2, h3, h4 { font-weight: 600 !important; letter-spacing: -0.025em; color: var(--tinta) !important; }
.block-container { max-width: 960px; padding-top: 3rem; padding-bottom: 5rem; }
html body .stApp :is(.titulo, .titulo *, .cabecera-sesion h2 *, .cap-num, .cap-titulo, .indice-num, .indice-nombre, .rol-nombre, .res-txt, .res-txt em, .cabecera-sesion h2, .filete i, [data-testid="stSidebar"] h3, [data-testid="stSidebar"] h3 span):not(#_a):not(#_b) { font-family: var(--serif) !important; }

/* Portada */
.portada { text-align: center; padding: 3.5rem 0 1rem; }
.sello { display: inline-block; font-size: .72rem; font-weight: 600; letter-spacing: .22em; text-transform: uppercase; color: var(--oliva);
  border-top: 1px solid var(--oliva); border-bottom: 1px solid var(--oliva); padding: .45rem 1rem; margin-bottom: 2.2rem; }
.titulo { font-size: clamp(2.6rem, 7.2vw, 5.2rem) !important; line-height: .95 !important; font-weight: 500 !important; letter-spacing: -0.02em !important; margin: 0 !important; color: var(--tinta) !important; }
.titulo em { font-style: italic; color: var(--oliva); font-weight: 500; }
.filete { display: flex; align-items: center; justify-content: center; gap: 1rem; margin: 2.2rem auto 1.8rem; max-width: 300px; }
.filete span { flex: 1; height: 1px; background: var(--linea); }
.filete i { font-style: normal; color: var(--salvia); font-size: 1.3rem; }
.bajada { font-size: 1.15rem !important; color: var(--gris) !important; max-width: 600px; margin: 0 auto !important; line-height: 1.65 !important; }
.autoria { margin-top: 1.8rem; font-size: .9rem; color: var(--gris); letter-spacing: .01em; }
.autoria strong { color: var(--tinta); font-weight: 600; }
.demo { display: inline-block; margin-top: 1.2rem; font-size: .75rem; color: var(--oliva); background: var(--oliva-claro); border-radius: 999px; padding: .3rem .9rem; }

/* Capítulos */
.capitulo { display: flex; align-items: baseline; gap: 1.2rem; margin: 4.5rem 0 1.4rem; padding-bottom: 1rem; border-bottom: 1px solid var(--tinta); }
.cap-num { font-size: 2.6rem; font-style: italic; color: var(--oliva); line-height: 1; min-width: 2.6rem; font-weight: 500; }
.cap-titulo { font-size: 2rem; font-weight: 600; letter-spacing: -0.015em; line-height: 1.1; color: var(--tinta); }
.cap-sub { font-size: .92rem; color: var(--gris); margin-top: .3rem; }

/* Índice de escuelas */
[data-testid="stHorizontalBlock"]:has(.indice-num) { border-bottom: 1px solid var(--linea); padding: 1rem .6rem; margin: 0 !important; transition: background .2s ease; border-radius: 0; }
[data-testid="stHorizontalBlock"]:has(.indice-num):hover { background: rgba(61,79,61,.035); }
[data-testid="stHorizontalBlock"]:has(.fila-elegida) { background: var(--cita-fondo); box-shadow: inset 3px 0 0 var(--oliva); }
.indice-num { font-size: 1.9rem; font-style: italic; color: #A4AE9F; text-align: center; font-weight: 500; }
.fila-elegida.indice-num { color: var(--oliva); }
.indice-nombre { font-size: 1.65rem; font-weight: 600; letter-spacing: -0.01em; line-height: 1.15; color: var(--tinta); }
.indice-lema { font-size: .92rem; color: var(--gris); margin-top: .2rem; line-height: 1.5; }
.indice-periodo { display: block; color: #9A9A9F; font-size: .78rem; letter-spacing: .08em; text-transform: uppercase; margin-top: .25rem; }

/* Roles */
[data-testid="stVerticalBlock"]:has(> [data-testid="stElementContainer"] .rol-nombre) {
  background: var(--tarjeta); border: 1px solid var(--linea) !important; border-radius: 16px !important; box-shadow: var(--sombra);
  padding: 1.6rem 1.4rem 1.3rem; transition: box-shadow .2s ease, transform .2s ease, border-color .2s ease;
}
[data-testid="stVerticalBlock"]:has(> [data-testid="stElementContainer"] .rol-nombre):hover { box-shadow: 0 10px 30px rgba(0,0,0,.06); transform: translateY(-2px); }
[data-testid="stVerticalBlock"]:has(> [data-testid="stElementContainer"] .rol-elegido) { border-color: var(--oliva) !important; box-shadow: 0 0 0 1px var(--oliva), var(--sombra); }
.rol-pre { font-size: .72rem; font-weight: 600; letter-spacing: .16em; text-transform: uppercase; color: var(--salvia); }
.rol-nombre { font-size: 2.4rem; font-style: italic; font-weight: 500; line-height: 1.05; color: var(--tinta); margin: .15rem 0 .8rem; }
.rol-texto { font-size: .93rem; color: var(--gris); line-height: 1.6; min-height: 6.2rem; }
.rol-meta { font-size: .78rem; color: #9A9A9F; border-top: 1px solid var(--linea); padding-top: .7rem; margin: .6rem 0 .3rem; }

/* Resumen y comenzar */
.resumen { display: flex; flex-direction: column; gap: .2rem; }
.res-et { font-size: .72rem; font-weight: 600; letter-spacing: .16em; text-transform: uppercase; color: var(--salvia); }
.res-txt { font-size: 1.9rem; font-weight: 600; line-height: 1.15; color: var(--tinta); letter-spacing: -0.01em; }
.res-txt em { font-style: italic; font-weight: 500; color: var(--oliva); }
.res-vacio { color: #B0B0B4 !important; font-style: italic; font-weight: 500; }

/* Botones */
.stButton button, .stDownloadButton button {
  border-radius: 999px !important; font-weight: 500 !important; padding: .5rem 1.2rem !important;
  border: 1px solid var(--linea) !important; background: #FFF !important; color: var(--tinta) !important; box-shadow: none !important;
  transition: background .15s ease, border-color .15s ease, color .15s ease;
}
.stButton button:hover, .stDownloadButton button:hover { border-color: var(--oliva) !important; color: var(--oliva) !important; }
.stButton button[kind="primary"] { background: var(--oliva) !important; border-color: var(--oliva) !important; color: #FFF !important; }
.stButton button[kind="primary"] p { color: #FFF !important; }
.stButton button[kind="primary"]:hover { background: var(--salvia) !important; border-color: var(--salvia) !important; }
.stButton button:disabled { background: #EDEDE8 !important; border-color: #EDEDE8 !important; }
.stButton button:disabled p { color: #A0A0A4 !important; }
.st-key-comenzar button { padding: .85rem 1.4rem !important; font-size: 1.05rem !important; }

/* Avisos */
.aviso { font-size: .82rem; color: var(--gris); border-left: 2px solid var(--linea); padding: .2rem 0 .2rem 1rem; margin: 1.6rem 0 1.2rem; line-height: 1.6; }
[data-testid="stExpander"] { border: none !important; border-top: 1px solid var(--linea) !important; border-bottom: 1px solid var(--linea) !important; border-radius: 0 !important; background: transparent; }
[data-testid="stExpander"] summary p { font-weight: 500; }
[data-testid="stAlertContainer"] { border-radius: 12px !important; background: var(--cita-fondo) !important; color: var(--oliva) !important; }

/* Colofón */
.colofon { text-align: center; font-family: var(--serif) !important; font-size: 1.15rem; font-style: italic; color: var(--tinta); margin-top: 4rem; line-height: 1.6; }
.colofon span { font-family: var(--sans) !important; font-style: normal; font-size: .76rem; color: var(--gris); letter-spacing: .02em; }

/* Sesión */
.eyebrow { font-size: .72rem; font-weight: 600; letter-spacing: .16em; text-transform: uppercase; color: var(--salvia); margin-bottom: .4rem; }
.cabecera-sesion { border-bottom: 1px solid var(--tinta); padding: 1.5rem 0 1rem; margin: 0 0 1.6rem; }
.cabecera-sesion h2 { margin: 0; font-size: 3.4rem !important; font-weight: 500 !important; font-style: italic; line-height: 1; letter-spacing: -0.015em; }
[data-testid="stChatMessage"] { background: var(--tarjeta); border: 1px solid var(--linea); border-radius: 16px; box-shadow: var(--sombra); padding: 1.2rem 1.4rem; margin-bottom: 1rem; }
[data-testid="stChatMessage"]:has(.msg-user) { background: transparent; border: none; box-shadow: none; padding: .4rem 1.4rem .4rem 3.2rem; }
[data-testid="stChatMessage"]:has(.msg-user) p { font-weight: 500; color: var(--oliva); }
[data-testid="stElementContainer"]:has(.msg-user), .msg-user { display: none; }
[data-testid="stChatMessageAvatarCustom"] { background: var(--cita-fondo) !important; border-radius: 50%; }

/* Citas */
.stApp blockquote { background: var(--cita-fondo) !important; border-left: 3px solid var(--oliva) !important; border-radius: 0 12px 12px 0 !important;
  padding: 1.1rem 1.5rem !important; margin: 1.3rem 0 !important; opacity: 1 !important; }
html body .stApp blockquote, html body .stApp blockquote :is(p,span,em,strong,div):not([data-testid="stIconMaterial"]):not(.material-symbols-rounded):not(.x-georgia) {
  font-family: "Georgia", serif !important; font-size: 1.04rem; line-height: 1.65; color: #2C3A2C !important; }

/* Entrada */
[data-testid="stBottom"] > div { background: var(--fondo); }
[data-testid="stChatInput"] { border-radius: 999px !important; border: 1px solid var(--linea) !important; background: #FFF !important; box-shadow: var(--sombra); }
[data-testid="stChatInput"]:focus-within { border-color: var(--salvia) !important; }
[data-testid="stChatInputSubmitButton"] { background: var(--oliva) !important; border-radius: 999px !important; color: #FFF !important; }

/* Barra lateral */
[data-testid="stSidebar"] { background: var(--lateral); border-right: 1px solid var(--linea); }
[data-testid="stSidebar"] h3 { font-size: 2.1rem !important; font-weight: 500 !important; font-style: italic; margin-top: .1rem; line-height: 1.05; }
[data-testid="stSidebar"] h4 { font-size: .72rem !important; letter-spacing: .16em; text-transform: uppercase; color: var(--salvia) !important; margin-top: 1.6rem; border-top: 1px solid var(--linea); padding-top: 1.2rem; }
.chip { display: inline-block; padding: .22rem .7rem; border-radius: 999px; background: #FFF; border: 1px solid var(--linea); color: var(--tinta); font-size: .76rem; margin: 0 .3rem .3rem 0; }
.ficha dt { font-weight: 600; color: var(--oliva); font-size: .7rem; text-transform: uppercase; letter-spacing: .1em; margin-top: 1rem; }
.ficha dd { margin: .2rem 0 0 0; color: var(--tinta); font-size: .9rem; line-height: 1.6; }
[data-testid="stProgress"] > div > div > div > div { background: var(--oliva) !important; }
.credito { margin-top: 2rem; font-size: .76rem; color: var(--gris); line-height: 1.5; }
.credito strong { font-family: var(--serif) !important; font-style: italic; font-size: 1.05rem; color: var(--tinta); font-weight: 600; }

@media (max-width: 640px) { .titulo { font-size: 3.2rem !important; } .cap-titulo { font-size: 1.6rem; } }
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
NUMERALES = ["I", "II", "III", "IV", "V", "VI"]
AUTOR = "Alexander Tobón Arias"


def pantalla_inicio():
    demo = "" if hay_clave() else "<span class='demo'>Modo demostración · respuestas de ejemplo</span>"
    st.markdown(
        f"""
<header class="portada">
  <div class="sello">Taller con inteligencia artificial</div>
  <h1 class="titulo">Historia del<br><em>pensamiento económico</em></h1>
  <div class="filete"><span></span><i>❦</i><span></span></div>
  <p class="bajada">Seis escuelas y tres maneras de conversar con la IA para reconstruir cada teoría desde sus propios problemas.
  La IA pregunta, se equivoca a propósito o te sitúa en la historia; el razonamiento es tuyo.</p>
  <div class="autoria">Un proyecto de <strong>{AUTOR}</strong></div>
  {demo}
</header>
""",
        unsafe_allow_html=True,
    )

    # I. Escuela
    st.markdown(
        "<div class='capitulo'><span class='cap-num'>I</span><div><div class='cap-titulo'>Elige una escuela</div>"
        "<div class='cap-sub'>Seis tradiciones, de los mercaderes del siglo XVI a Keynes.</div></div></div>",
        unsafe_allow_html=True,
    )
    for n, (eid, e) in zip(NUMERALES, ESCUELAS.items()):
        elegida = ss.escuela == eid
        with st.container():
            marca = "fila-elegida" if elegida else "fila"
            c1, c2, c3 = st.columns([0.55, 4.2, 1.45], vertical_alignment="center")
            c1.markdown(f"<div class='{marca} indice-num'>{n}</div>", unsafe_allow_html=True)
            c2.markdown(
                f"<div class='indice-nombre'>{e['nombre']}</div>"
                f"<div class='indice-lema'>{e['lema']} <span class='indice-periodo'>{e['periodo']}</span></div>",
                unsafe_allow_html=True,
            )
            if c3.button("Elegida ✓" if elegida else "Elegir", key=f"esc_{eid}",
                         type="primary" if elegida else "secondary", use_container_width=True):
                ss.escuela = eid
                st.rerun()

    # II. Rol
    st.markdown(
        "<div class='capitulo'><span class='cap-num'>II</span><div><div class='cap-titulo'>Elige el papel de la IA</div>"
        "<div class='cap-sub'>Según Mollick y Mollick (2023), adaptados al método de Marcuzzo (2008).</div></div></div>",
        unsafe_allow_html=True,
    )
    cols = st.columns(len(ROLES), gap="medium")
    for col, (rid, r) in zip(cols, ROLES.items()):
        elegido = ss.rol == rid
        with col.container(border=True):
            st.markdown(
                f"<div class='{'rol-elegido' if elegido else 'rol'}'></div>"
                f"<div class='rol-pre'>La IA como</div>"
                f"<div class='rol-nombre'>{r['nombre'].lower()}</div>"
                f"<div class='rol-texto'>{r['resumen']}</div>"
                f"<div class='rol-meta'>Hasta {r['max_intercambios']} intercambios</div>",
                unsafe_allow_html=True,
            )
            if st.button("Elegido ✓" if elegido else "Elegir", key=f"rol_{rid}",
                         type="primary" if elegido else "secondary", use_container_width=True):
                ss.rol = rid
                st.rerun()

    # III. Comenzar
    st.markdown(
        "<div class='capitulo'><span class='cap-num'>III</span><div><div class='cap-titulo'>Comienza la sesión</div>"
        "<div class='cap-sub'>Al terminar, descarga la conversación y entrégala con tu reflexión.</div></div></div>",
        unsafe_allow_html=True,
    )
    listo = ss.escuela and ss.rol
    if listo:
        resumen = (f"<span class='res-et'>Tu sesión</span><span class='res-txt'>{ESCUELAS[ss.escuela]['nombre']}"
                   f" <em>con la IA como {ROLES[ss.rol]['nombre'].lower()}</em></span>")
    else:
        resumen = "<span class='res-et'>Tu sesión</span><span class='res-txt res-vacio'>Elige una escuela y un papel para la IA</span>"
    c1, c2 = st.columns([2.6, 1.4], vertical_alignment="center")
    c1.markdown(f"<div class='resumen'>{resumen}</div>", unsafe_allow_html=True)
    with c2:
        if st.button("Comenzar →", type="primary", disabled=not listo, use_container_width=True, key="comenzar"):
            iniciar_sesion()
            st.rerun()
    st.markdown(f"<div class='aviso'>{AVISO_PRIVACIDAD}</div>", unsafe_allow_html=True)

    with st.expander("Las tres intencionalidades formativas del curso"):
        for k, v in INTENCIONALIDADES.items():
            st.markdown(f"**{k.capitalize()}.** {v}")

    st.markdown(
        f"<footer class='colofon'><div class='filete'><span></span><i>❦</i><span></span></div>"
        f"Historia del pensamiento económico · {AUTOR}<br>"
        f"<span>Roles de Mollick y Mollick (2023) · Método de Marcuzzo (2008)</span></footer>",
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
        st.markdown(f"<div class='credito'>Historia del pensamiento económico<br><strong>{AUTOR}</strong></div>",
                    unsafe_allow_html=True)

    # Cabecera
    st.markdown(
        f"<div class='cabecera-sesion'><div class='eyebrow'>La IA como {r['nombre'].lower()} · {e['periodo']}</div>"
        f"<h2>{e['nombre']}</h2></div>",
        unsafe_allow_html=True,
    )
    if not hay_clave():
        st.markdown("<span class='demo'>Modo demostración · respuestas de ejemplo</span>", unsafe_allow_html=True)

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
