"""
Conexión con el modelo de lenguaje (API de Gemini, nivel gratuito).

La clave se configura como secreto, nunca en el código:
    .streamlit/secrets.toml  →  GEMINI_API_KEY = "..."
Sin clave, la app funciona en MODO DEMOSTRACIÓN con respuestas de ejemplo.
"""
from __future__ import annotations

import os

import streamlit as st

MODELO_POR_DEFECTO = "gemini-flash-latest"


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

    return genai.Client(api_key=clave)


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

    try:
        r = cliente.models.generate_content(
            model=_secreto("GEMINI_MODEL", MODELO_POR_DEFECTO),
            contents=contenidos,
            config=types.GenerateContentConfig(
                system_instruction=f"{prompt_sistema}\n\n{contexto}",
                temperature=0.6,
                max_output_tokens=900,
            ),
        )
        return r.text or "No obtuve respuesta. ¿Puedes intentarlo de nuevo?"
    except Exception as err:  # límite de cuota, clave, modelo, red, etc.
        texto = str(err)
        codigo = getattr(err, "code", None)
        print(f"[modelo] Error de Gemini: {type(err).__name__} {codigo}: {texto[:500]}", flush=True)
        if codigo == 429 or "RESOURCE_EXHAUSTED" in texto:
            return ("⏳ Se alcanzó por ahora el límite gratuito de consultas de la app. "
                    "Espera unos minutos e inténtalo de nuevo.")
        if "API_KEY_INVALID" in texto or "API key not valid" in texto or codigo == 401:
            return ("⚠️ La clave de Gemini no es válida. Revisa el valor de GEMINI_API_KEY en los Secrets "
                    "(comillas rectas, sin espacios) o crea una clave nueva en aistudio.google.com.")
        if codigo == 403:
            return ("⚠️ La clave de Gemini no tiene permiso para usar el modelo (error 403). "
                    "Revisa en aistudio.google.com que la clave esté activa y sin restricciones.")
        if codigo == 404:
            return ("⚠️ El modelo configurado no está disponible (error 404). "
                    "Revisa el valor de GEMINI_MODEL en los Secrets o bórralo para usar el modelo por defecto.")
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
    "energías originarias e indestructibles del suelo» [Fuente: Ricardo, Principios, cap. 2]\n\n"
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
