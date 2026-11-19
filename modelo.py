"""
Conexión con el modelo de lenguaje (API de Gemini, nivel gratuito).

La clave se configura como secreto, nunca en el código:
    .streamlit/secrets.toml  →  GEMINI_API_KEY = "..."
Sin clave, la app funciona en MODO DEMOSTRACIÓN con respuestas de ejemplo.
"""
from __future__ import annotations

import os
import time

import streamlit as st

# Modelos que se prueban en orden. Si uno está saturado (503), no existe para la
# clave (404) o agotó su cuota gratuita (429), la app pasa al siguiente.
# Si todos fallan, la app pregunta a Google qué modelos "flash" tiene la clave y los prueba.
# Para fijar otro primero, agregue GEMINI_MODEL = "..." en los Secrets.
_ULTIMO_QUE_FUNCIONO: dict = {}  # se recuerda entre consultas para no repetir modelos saturados

MODELOS = [
    "gemini-3.7-flash", "gemini-3.6-flash", "gemini-3.5-flash", "gemini-3.8-flash",
    "gemini-3.5-flash-lite", "gemini-3.1-flash-lite", "gemini-2.5-flash", "gemini-2.5-flash-lite",
]


def _secreto(nombre: str, defecto: str | None = None) -> str | None:
    try:
        if nombre in st.secrets:
            return st.secrets[nombre]
    except Exception:  # sin archivo de secretos
        pass
    return os.environ.get(nombre, defecto)


def hay_clave() -> bool:
    return bool(_secreto("GEMINI_API_KEY"))


@st.cache_resource(show_spinner=False)
def _cliente(clave: str):
    from google import genai
    from google.genai import types

    # Sin reintentos automáticos de la librería (la app ya prueba otros modelos)
    # y con un tiempo máximo por intento, para que una saturación no deje la app colgada.
    return genai.Client(
        api_key=clave,
        http_options=types.HttpOptions(timeout=60_000, retry_options=types.HttpRetryOptions(attempts=1)),
    )


def responder(prompt_sistema: str, contexto: str, historial: list[dict]) -> str:
    """historial: [{'role': 'user'|'assistant', 'content': str}, ...]"""
    if not hay_clave():
        return _respuesta_demo(historial)

    from google.genai import types

    cliente = _cliente(_secreto("GEMINI_API_KEY"))
    contenidos = [
        types.Content(
            role="model" if m["role"] == "assistant" else "user",
            parts=[types.Part(text=m["content"])],
        )
        for m in historial
    ]
    if not contenidos:  # La IA abre la conversación, como en los prompts de Mollick
        contenidos = [types.Content(role="user", parts=[types.Part(text="Hola, empecemos.")])]

    base = dict(
        system_instruction=f"{prompt_sistema}\n\n{contexto}",
        temperature=0.6,
        max_output_tokens=2048,
    )
    # Los modelos 3.x "piensan" antes de responder; con razonamiento bajo responden mucho más rápido.
    config_rapida = types.GenerateContentConfig(**base, thinking_config=types.ThinkingConfig(thinking_level="LOW"))
    config_simple = types.GenerateContentConfig(**base)

    preferido = _secreto("GEMINI_MODEL")
    primeros = [m for m in (_ULTIMO_QUE_FUNCIONO.get("modelo"), preferido) if m]
    modelos = list(dict.fromkeys(primeros + MODELOS))  # primero el último que respondió bien

    errores = []
    probados = set()
    inicio = time.monotonic()

    def intentar(lista):
        for modelo in lista:
            if modelo in probados:
                continue
            probados.add(modelo)
            if time.monotonic() - inicio > 100:
                print("[modelo] Se agotó el tiempo total de espera.", flush=True)
                return None
            for intento in range(1):
                try:
                    try:
                        r = cliente.models.generate_content(model=modelo, contents=contenidos, config=config_rapida)
                    except Exception as err_cfg:
                        if getattr(err_cfg, "code", None) != 400:
                            raise
                        # el modelo no acepta el ajuste de razonamiento: se pide sin él
                        r = cliente.models.generate_content(model=modelo, contents=contenidos, config=config_simple)
                    _ULTIMO_QUE_FUNCIONO["modelo"] = modelo
                    return r.text or "No obtuve respuesta. ¿Puedes intentarlo de nuevo?"
                except Exception as err:
                    errores.append(err)
                    codigo = getattr(err, "code", None)
                    print(f"[modelo] {modelo}: {type(err).__name__} {codigo}: {str(err)[:300]}", flush=True)
                    break
            codigo = getattr(errores[-1], "code", None)
            if not (codigo in (404, 429, 500, 503, 504) or "RESOURCE_EXHAUSTED" in str(errores[-1])):
                return None  # error de clave o de solicitud: no sirve cambiar de modelo
        return None

    texto = intentar(modelos)
    if texto is None and all(getattr(e, "code", None) in (404, 429, 500, 503, 504) for e in errores):
        texto = intentar(_modelos_de_la_clave(cliente))
    return texto if texto is not None else _mensaje_error(errores)


@st.cache_resource(show_spinner=False, ttl=3600)
def _modelos_de_la_clave(_cliente) -> list[str]:
    """Modelos 'flash' de texto que Google ofrece para esta clave, del más nuevo al más viejo."""
    try:
        nombres = []
        for m in _cliente.models.list():
            nombre = m.name.split("/")[-1]
            acciones = getattr(m, "supported_actions", None) or []
            if "flash" in nombre and not any(x in nombre for x in ("image", "tts", "audio", "live", "embedding")) \
                    and (not acciones or "generateContent" in acciones):
                nombres.append(nombre)
        return sorted(nombres, reverse=True)
    except Exception as err:
        print(f"[modelo] No pude listar los modelos: {err}", flush=True)
        return []


def _mensaje_error(errores) -> str:
    codigos = [getattr(e, "code", None) for e in errores]
    if any(c in (500, 503, 504) for c in codigos):
        return ("⏳ Los modelos de Google están muy solicitados en este momento. "
                "Espera un minuto y vuelve a enviar tu mensaje.")
    if 429 in codigos or any("RESOURCE_EXHAUSTED" in str(e) for e in errores):
        return ("⏳ Se alcanzó por ahora el límite gratuito de consultas de la app. "
                "Espera unos minutos e inténtalo de nuevo.")
    err = errores[-1] if errores else None
    texto = str(err)
    codigo = getattr(err, "code", None)
    if codigo == 429 or "RESOURCE_EXHAUSTED" in texto:
        return ("⏳ Se alcanzó por ahora el límite gratuito de consultas de la app. "
                "Espera unos minutos e inténtalo de nuevo.")
    if codigo in (500, 503) or "UNAVAILABLE" in texto:
        return ("⏳ Los modelos de Google están saturados en este momento. "
                "Espera un minuto e inténtalo de nuevo.")
    if "API_KEY_INVALID" in texto or "API key not valid" in texto or codigo == 401:
        return ("⚠️ La clave de Gemini no es válida. Revisa el valor de GEMINI_API_KEY en los Secrets "
                "(comillas rectas, sin espacios) o crea una clave nueva en aistudio.google.com.")
    if codigo == 403:
        return ("⚠️ La clave de Gemini no tiene permiso para usar el modelo (error 403). "
                "Revisa en aistudio.google.com que la clave esté activa y sin restricciones.")
    if codigo == 404:
        return ("⚠️ Ninguno de los modelos configurados está disponible para esta clave (error 404). "
                "Revisa la lista MODELOS en modelo.py.")
    detalle = getattr(err, "message", None) or texto
    return (f"⚠️ No pude conectarme con el modelo ({type(err).__name__} {codigo or ''}). "
            f"Detalle: {str(detalle)[:220]}")


# ---------------------------------------------------------------------------
# Modo demostración: respuestas fijas para revisar la interfaz sin clave
# ---------------------------------------------------------------------------
_DEMO = [
    "¡Hola! Soy tu tutor para esta sesión. Antes de empezar, cuéntame: **¿qué sabes ya de esta escuela?** "
    "Puede ser un autor, una idea o un problema que recuerdes de clase.",
    "Buen punto de partida. Vamos a afinarlo: si la tierra de mejor calidad es limitada y la población crece, "
    "¿qué tiene que pasar con las tierras que se ponen en cultivo? Piensa en su fertilidad.\n\n"
    "> «La renta es aquella porción del producto de la tierra que se paga al terrateniente por el uso de las "
    "energías originarias e indestructibles del suelo» [Ricardo, Principios (1817), cap. 2]\n\n"
    "Con esa definición en mente, **¿de dónde crees que sale la renta: de la tierra más fértil o de la diferencia "
    "entre tierras?**",
    "Exacto, la clave está en la diferencia. Ahora explícalo con tus propias palabras: "
    "**¿por qué, según este modelo, la renta es un efecto del precio del grano y no su causa?**",
]


def _respuesta_demo(historial: list[dict]) -> str:
    n = sum(1 for m in historial if m["role"] == "assistant")
    if n < len(_DEMO):
        return _DEMO[n]
    return ("*(Modo demostración)* Aquí respondería el modelo de IA. "
            "Para activarlo, configura la clave GEMINI_API_KEY como se explica en el README.")
