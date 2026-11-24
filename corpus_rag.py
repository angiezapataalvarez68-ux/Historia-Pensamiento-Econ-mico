"""
Búsqueda en el corpus del curso (RAG cerrado).

Cada escuela tiene una carpeta en corpus/<escuela>/ con las obras originales.
Los comentarios académicos (libros y artículos de especialistas) van en:
    corpus/comentarios/            → se usan con todas las escuelas
    corpus/comentarios/<escuela>/  → solo con esa escuela
Se aceptan archivos .md, .txt, .pdf y .docx.
La ficha de la escuela (Cuadro 2) siempre forma parte del corpus como orientación interna.

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
    tipo: str = "obra"  # "obra" (fuente primaria) o "comentario" (interpretación académica)


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


def _leer_pdf(archivo: Path) -> str:
    from pypdf import PdfReader
    paginas = [pag.extract_text() or "" for pag in PdfReader(str(archivo)).pages]
    # En los PDF los párrafos vienen cortados por renglones: se unen las líneas y se
    # separa en párrafos donde hay un punto final al terminar la línea.
    texto = "\n".join(paginas).replace("-\n", "")
    texto = re.sub(r"(?<![.:;!?»”])\n(?!\n)", " ", texto)
    return texto.replace("\n", "\n\n")


def _leer_docx(archivo: Path) -> str:
    import zipfile
    from xml.etree import ElementTree as ET
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    with zipfile.ZipFile(archivo) as z:
        raiz = ET.fromstring(z.read("word/document.xml"))
    parrafos = ["".join(t.text or "" for t in p.iter(f"{{{ns['w']}}}t")) for p in raiz.iter(f"{{{ns['w']}}}p")]
    return "\n\n".join(p for p in parrafos if p.strip())


def _leer_archivo(archivo: Path) -> tuple[str, str] | None:
    """Devuelve (fuente, cuerpo) o None si el archivo no es del corpus."""
    sufijo = archivo.suffix.lower()
    if archivo.name.lower().startswith("leeme") or sufijo not in {".md", ".txt", ".pdf", ".docx"}:
        return None
    try:
        if sufijo == ".pdf":
            contenido = _leer_pdf(archivo)
        elif sufijo == ".docx":
            contenido = _leer_docx(archivo)
        else:
            contenido = archivo.read_text(encoding="utf-8")
    except Exception as err:  # un archivo dañado no debe tumbar la app
        print(f"[corpus] No pude leer {archivo.name}: {err}", flush=True)
        return None
    lineas = contenido.splitlines()
    if lineas and lineas[0].startswith("# "):
        fuente, cuerpo = lineas[0][2:].strip(), "\n".join(lineas[1:])
    else:
        fuente, cuerpo = archivo.stem.replace("_", " "), contenido
    # La nota bibliográfica en cursiva (_..._) no es texto de la obra: no se indexa.
    cuerpo = re.sub(r"^_.*_\s*$", "", cuerpo, flags=re.M)
    return fuente, cuerpo


def cargar_fragmentos(escuela_id: str) -> list[Fragmento]:
    fragmentos = [_ficha(escuela_id)]
    fuentes = [(CORPUS_DIR / escuela_id, "obra"),
               (CORPUS_DIR / "comentarios", "comentario"),
               (CORPUS_DIR / "comentarios" / escuela_id, "comentario")]
    for carpeta, tipo in fuentes:
        if not carpeta.exists():
            continue
        for archivo in sorted(carpeta.glob("*")):
            if not archivo.is_file():
                continue
            leido = _leer_archivo(archivo)
            if leido:
                fuente, cuerpo = leido
                fragmentos += [Fragmento(fuente, t, tipo) for t in _partir(cuerpo)]
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
    # Términos nuevos (2026-11): banca, marginalismo, institucionalismo
    "banco central": "bank of england reserve lender", "prestamista": "lender last resort advance", "reserva": "reserve reserves",
    "credito": "credit bills", "billete": "bank notes paper currency", "oro": "gold bullion", "deprecia": "depreciation",
    "margin": "margin marginal final degree of utility", "intercambio": "exchange", "preferencia temporal": "present future goods",
    "rodeo": "roundabout methods", "produccion indirecta": "roundabout methods", "productividad marginal": "final productivity specific product",
    "consumo ostentoso": "conspicuous consumption", "ocio": "leisure", "clase ociosa": "leisure class", "empresa": "business enterprise",
    "fuerzas productivas": "productive powers", "proteccion": "protection protective", "metodo": "method logical",
    "tasa natural": "natural rate", "abstinencia": "abstinence",
}

# Algunas obras del corpus están en alemán (Marx, Theorien über den Mehrwert; Luxemburg; Hilferding):
# se añaden los términos alemanes para que la búsqueda también las encuentre.
GLOSARIO_DE = {
    "plusvalia": "Mehrwert", "acumulacion": "Akkumulation akkumulieren", "reproduccion": "Reproduktion",
    "crisis": "Krise Krisen Überproduktion", "sobreproduccion": "Überproduktion", "trabajo productivo": "produktive Arbeit",
    "trabajo improductivo": "unproduktive Arbeit", "capital financiero": "Finanzkapital", "banco": "Bank Banken Bankkapital",
    "monopolio": "Monopol Monopole Kartelle", "cartel": "Kartelle Trusts", "imperialismo": "Imperialismus Kapitalexport",
    "exportacion de capital": "Kapitalexport", "tasa de ganancia": "Profitrate", "ganancia": "Profit", "valor": "Wert",
    "precio": "Preis", "salario": "Arbeitslohn", "mercado": "Markt Absatz", "consum": "Konsumtion", "renta": "Rente Grundrente",
}
for _es, _de in GLOSARIO_DE.items():
    GLOSARIO[_es] = (GLOSARIO.get(_es, "") + " " + _de).strip()


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

    def buscar(self, consulta: str, k: int = 5, k_comentarios: int = 2) -> list[Fragmento]:
        """La ficha va primero; luego los k pasajes de obras y hasta k_comentarios comentarios más parecidos."""
        resultado = [self.fragmentos[0]]
        if len(self.fragmentos) == 1 or not consulta.strip():
            return resultado
        sims = cosine_similarity(self.vectorizador.transform([_expandir(consulta)]), self.matriz).ravel()
        orden = sims[1:].argsort()[::-1] + 1
        obras = [i for i in orden if self.fragmentos[i].tipo == "obra" and sims[i] > 0.02][:k]
        coments = [i for i in orden if self.fragmentos[i].tipo == "comentario" and sims[i] > 0.02][:k_comentarios]
        return resultado + [self.fragmentos[i] for i in obras + coments]


def formatear_contexto(fragmentos: list[Fragmento]) -> str:
    """La ficha del curso va aparte, como orientación interna que no se cita."""
    ficha = [f for f in fragmentos if f.fuente.startswith("Ficha del curso")]
    obras = [f for f in fragmentos if f.tipo == "obra" and not f.fuente.startswith("Ficha del curso")]
    coments = [f for f in fragmentos if f.tipo == "comentario"]
    partes = []
    if ficha:
        partes.append("ORIENTACIÓN INTERNA DEL CURSO (no es una fuente: úsala para guiar la conversación, "
                      "pero NUNCA la cites ni la menciones como fuente):\n" + ficha[0].texto)
    if obras:
        partes.append("PASAJES DE LAS OBRAS ORIGINALES (fuentes primarias; cítalas textualmente):")
        partes += [f"[{i}] Obra: {f.fuente}\n{f.texto}" for i, f in enumerate(obras, 1)]
    if coments:
        partes.append("COMENTARIOS ACADÉMICOS (interpretaciones de especialistas; si los usas, cítalos como "
                      "interpretación del comentarista, nunca como palabras del autor estudiado):")
        partes += [f"[C{i}] Comentario: {f.fuente}\n{f.texto}" for i, f in enumerate(coments, 1)]
    if not obras and not coments:
        partes.append("No se encontraron pasajes para esta consulta: no inventes citas; "
                      "pide al estudiante que precise la pregunta o razona sin citar.")
    return "\n\n".join(partes)
