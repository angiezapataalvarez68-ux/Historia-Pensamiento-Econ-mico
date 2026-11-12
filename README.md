# Historia del pensamiento económico · Taller con IA

Proyecto de Alexander Tobón Arias.

App para el trabajo independiente del curso de Historia del Pensamiento Económico.
Tobón y Zapata (2026). Roles de Mollick y Mollick (2023); método de Marcuzzo (2008).

El estudiante elige una escuela (las seis del Cuadro 2) y un rol de la IA (tutor, estudiante o simulador). La app carga el prompt del Cuadro 3, busca en el corpus de la escuela los pasajes relevantes y se los pasa al modelo, que debe citarlos textualmente. Al final, el estudiante descarga la conversación para entregarla con su reflexión.

No requiere cuentas para los estudiantes: abren el enlace y la usan.

## Estructura

| Archivo | Qué contiene |
|---|---|
| `app.py` | La interfaz (pantalla de selección y sesión de chat) |
| `contenido.py` | Escuelas, roles y los 18 prompts. **Aquí se editan los prompts.** |
| `corpus_rag.py` | Búsqueda de pasajes en el corpus (RAG cerrado) |
| `modelo.py` | Conexión con la API de Gemini y modo demostración |
| `corpus/<escuela>/` | Textos de cada escuela. Ver `corpus/LEEME.md` |

## Probar en el computador

```bash
pip install -r requirements.txt
streamlit run app.py
```

Sin clave, la app funciona en **modo demostración** con respuestas de ejemplo.

## Conectar la IA (gratis)

1. Entrar a https://aistudio.google.com con una cuenta de Google y crear una clave de API (no pide tarjeta).
2. Copiar `.streamlit/secrets.toml.ejemplo` como `.streamlit/secrets.toml` y pegar la clave.

## Publicar para los estudiantes (gratis)

1. Subir esta carpeta a un repositorio de GitHub (sin `secrets.toml`; el `.gitignore` ya lo excluye).
2. Entrar a https://share.streamlit.io, elegir el repositorio y `app.py`, y pulsar **Deploy**.
3. En **App settings → Secrets**, pegar el contenido de `secrets.toml`.
4. Compartir el enlace `https://<nombre>.streamlit.app` con los estudiantes.

## Advertencias

- **Privacidad:** en el nivel gratuito, Google puede usar el contenido para mejorar sus productos. La app avisa a los estudiantes que no escriban datos personales (Ley 1581 de 2012).
- **Límites:** el nivel gratuito tiene una cuota por proyecto, compartida por todos los estudiantes. Si se agota, la app muestra un aviso y hay que esperar.
- **Derechos de autor:** el repositorio es público. Solo cargar en `corpus/` textos de dominio público o materiales propios.
- **Inactividad:** la app gratuita se duerme tras 12 horas sin uso; el primer visitante la despierta en unos segundos.
