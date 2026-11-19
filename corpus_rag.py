"""
Búsqueda en el corpus del curso (RAG cerrado).

Cada escuela tiene una carpeta en corpus/<escuela>/ con archivos .md o .txt.
La ficha de la escuela (Cuadro 2) siempre forma parte del corpus.

Formato recomendado para cada archivo del corpus:
    La primera línea es el título de la fuente, precedido de "# ".
    Ejemplo:  # Ricardo, Principios de economía política y tributación, cap. 2
    El resto del archivo es el texto, separado en párrafos por líneas en blanco.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from contenido import ESCUELAS

CORPUS_DIR = Path(__file__).parent / "corpus"
MAX_PALABRAS_FRAGMENTO = 220


@dataclass
class Fragmento:
    fuente: str
    texto: str


def _normalizar(texto: str) -> str:
    texto = unicodedata.normalize("NFD", texto.lower())
    return "".join(c for c in texto if unicodedata.category(c) != "Mn")


def _ficha(escuela_id: str) -> Fragmento:
    e = ESCUELAS[escuela_id]
    alternativa = e["alternativa"] or "es la base de la teoría económica dominante"
    texto = (
        f"Problema central: {e['problema']}. "
        f"Visión e ideología: {e['vision']}. "
        f"Núcleo reconstruido en lenguaje actual: {e['nucleo']}. "
        f"Alternativa frente a la teoría dominante: {alternativa}."
    )
    return Fragmento(fuente=f"Ficha del curso: {e['nombre']} (Cuadro 2)", texto=texto)


def _partir(texto: str) -> list[str]:
    """Une párrafos hasta ~MAX_PALABRAS_FRAGMENTO palabras."""
    parrafos = [p.strip() for p in re.split(r"\n\s*\n", texto) if p.strip()]
    # Los párrafos demasiado largos se cortan por oraciones.
    cortos = []
    for p in parrafos:
        if len(p.split()) <= MAX_PALABRAS_FRAGMENTO:
            cortos.append(p)
            continue
        bloque = ""
        for oracion in re.split(r"(?<=[.;:!?])\s+", p):
            if bloque and len((bloque + " " + oracion).split()) > MAX_PALABRAS_FRAGMENTO:
                cortos.append(bloque)
                bloque = oracion
            else:
                bloque = f"{bloque} {oracion}".strip()
        if bloque:
            cortos.append(bloque)
    parrafos = cortos
    trozos, actual = [], ""
    for p in parrafos:
        # Los títulos y párrafos muy cortos se pegan al siguiente para no quedar solos.
        if actual and len(actual.split()) >= 40 and len((actual + " " + p).split()) > MAX_PALABRAS_FRAGMENTO:
            trozos.append(actual)
            actual = p
        else:
            actual = f"{actual}\n\n{p}" if actual else p
    if actual:
        trozos.append(actual)
    return trozos


def cargar_fragmentos(escuela_id: str) -> list[Fragmento]:
    fragmentos = [_ficha(escuela_id)]
    carpeta = CORPUS_DIR / escuela_id
    if not carpeta.exists():
        return fragmentos
    for archivo in sorted(carpeta.glob("*")):
        if archivo.suffix.lower() not in {".md", ".txt"} or archivo.name.lower() == "leeme.md":
            continue
        contenido = archivo.read_text(encoding="utf-8")
        lineas = contenido.splitlines()
        if lineas and lineas[0].startswith("# "):
            fuente, cuerpo = lineas[0][2:].strip(), "\n".join(lineas[1:])
        else:
            fuente, cuerpo = archivo.stem.replace("_", " "), contenido
        # La nota bibliográfica en cursiva (_..._) no es texto de la obra: no se indexa.
        cuerpo = re.sub(r"^_.*_\s*$", "", cuerpo, flags=re.M)
        fragmentos += [Fragmento(fuente, t) for t in _partir(cuerpo)]
    return fragmentos

# Las fuentes primarias están en su idioma original (casi todas en inglés) y los
# estudiantes preguntan en español. Para que la búsqueda las encuentre, la consulta
# se amplía con los términos ingleses equivalentes. Se puede ampliar esta lista.
GLOSARIO = {
    "renta": "rent landlord", "terrateniente": "landlord landlords", "tierra": "land soil",
    "fertil": "fertility fertile", "cultivo": "cultivation cultivated", "agricult": "agriculture husbandry",
    "ganancia": "profit profits", "beneficio": "profit profits", "interes": "interest",
    "salario": "wages wage", "jornal": "wages", "trabajo": "labour labor work", "trabajador": "labourer workmen",
    "obrero": "workmen labourers proletarians", "valor": "value", "precio": "price prices",
    "natural": "natural", "mercado": "market", "mercancia": "commodity commodities",
    "capital": "capital stock", "acumulacion": "accumulation accumulate", "ahorro": "parsimony saving",
    "productiv": "productive unproductive", "division del trabajo": "division of labour",
    "dinero": "money", "moneda": "money coin", "oro": "gold", "plata": "silver", "metal": "gold silver bullion",
    "tesoro": "treasure", "riqueza": "wealth riches", "comercio": "trade commerce", "exterior": "foreign trade",
    "exporta": "exportation export", "importa": "importation import", "balanza": "balance of trade",
    "arancel": "duties restraints", "proteccion": "restraints monopoly", "mercantil": "mercantile system",
    "colonia": "colonies", "excedente": "surplus net produce", "producto neto": "net produce",
    "clase": "class classes order", "esteril": "unproductive barren sterile", "fisiocra": "agricultural system oeconomists",
    "quesnay": "quesnai tableau", "tableau": "tableau oeconomique", "circulacion": "circulation",
    "poblacion": "population", "subsistencia": "subsistence food", "alimento": "food corn",
    "trigo": "corn wheat", "grano": "corn", "utilidad": "utility useful", "marginal": "final degree of utility",
    "intercambio": "exchange", "cambio": "exchange", "demanda": "demand", "oferta": "supply",
    "escasez": "scarcity scarce", "burgues": "bourgeoisie bourgeois", "proletari": "proletariat proletarians",
    "explotacion": "exploitation", "propiedad": "property", "lucha de clases": "class struggle",
    "crisis": "crises crisis", "maquina": "machinery machine", "industria": "industry manufacture",
    "ventaja comparativa": "comparative advantage foreign trade", "vino": "wine", "pano": "cloth",
    "impuesto": "taxes tax", "competencia": "competition",
    "plusvalia": "surplus-value surplus value", "plusvalor": "surplus-value", "fuerza de trabajo": "labour-power",
    "valor de uso": "use-value", "valor de cambio": "exchange-value", "jornada": "working-day",
    "ejercito de reserva": "industrial reserve army relative surplus population", "composicion organica": "composition of capital",
    "tasa de": "rate of", "capital constante": "constant capital", "capital variable": "variable capital",
    "fetichismo": "fetishism", "dinero-mercancia": "money commodity", "elasticidad": "elasticity",
    "equilibrio": "equilibrium", "excedente del consumidor": "consumer's surplus", "necesidades": "wants",
    "precio de oferta": "supply price", "precio de demanda": "demand price", "corto plazo": "short period",
    "largo plazo": "long period", "anticipos": "advances", "avances": "advances", "clase productiva": "productive class",
    "gastos esteriles": "sterile expenses", "vend": "sell sold exportation", "extranjer": "strangers foreign forraign",
    "compra": "buy consume importation", "subconsumo": "under-consumption underconsumption saving",
    "sobreproduccion": "glut overproduction general glut", "demanda efectiva": "effectual demand effective demand consumption",
    "ley de say": "markets glut produce demand", "ley de los mercados": "markets glut produce demand",
    "acumulacion originaria": "primitive accumulation", "mano invisible": "invisible hand", "imperialismo": "imperialism",
    "rendimientos decrecientes": "diminishing return", "rendimientos crecientes": "increasing return",
    "tasa de interes": "rate of interest", "moneda": "money coin", "aritmetica politica": "political arithmetick",
    "poblacion": "population people", "desempleo": "unemployed employment", "atesoramiento": "hoarding hoard", "consum": "consume consumption", "comerciante": "merchant merchants", "propietario": "proprietor proprietors", "agricultor": "cultivator farmer",
}


def _expandir(consulta: str) -> str:
    n = _normalizar(consulta)
    extra = [en for es, en in GLOSARIO.items() if es in n]
    return consulta + " " + " ".join(extra)


class Buscador:
    """Índice TF-IDF por escuela. Se construye una vez y se reutiliza."""

    def __init__(self, escuela_id: str):
        self.fragmentos = cargar_fragmentos(escuela_id)
        self.vectorizador = TfidfVectorizer(preprocessor=_normalizar, ngram_range=(1, 2), sublinear_tf=True)
        self.matriz = self.vectorizador.fit_transform(
            [f"{f.fuente} {f.texto}" for f in self.fragmentos]
        )

    @property
    def fuentes(self) -> list[str]:
        return sorted({f.fuente for f in self.fragmentos})

    def buscar(self, consulta: str, k: int = 5) -> list[Fragmento]:
        """La ficha siempre va primero; luego los k fragmentos más parecidos."""
        resultado = [self.fragmentos[0]]
        if len(self.fragmentos) == 1 or not consulta.strip():
            return resultado
        sims = cosine_similarity(self.vectorizador.transform([_expandir(consulta)]), self.matriz).ravel()
        orden = sims[1:].argsort()[::-1] + 1
        resultado += [self.fragmentos[i] for i in orden[:k] if sims[i] > 0.02]
        return resultado


def formatear_contexto(fragmentos: list[Fragmento]) -> str:
    """La ficha del curso va aparte, como orientación interna que no se cita."""
    ficha = [f for f in fragmentos if f.fuente.startswith("Ficha del curso")]
    obras = [f for f in fragmentos if not f.fuente.startswith("Ficha del curso")]
    partes = []
    if ficha:
        partes.append("ORIENTACIÓN INTERNA DEL CURSO (no es una fuente: úsala para guiar la conversación, "
                      "pero NUNCA la cites ni la menciones como fuente):\n" + ficha[0].texto)
    if obras:
        partes.append("PASAJES DE LAS OBRAS ORIGINALES (son las únicas fuentes que puedes citar, textualmente):")
        for i, f in enumerate(obras, 1):
            partes.append(f"[{i}] Obra: {f.fuente}\n{f.texto}")
    else:
        partes.append("No se encontraron pasajes de las obras para esta consulta: no inventes citas; "
                      "pide al estudiante que precise la pregunta o razona sin citar.")
    return "\n\n".join(partes)
