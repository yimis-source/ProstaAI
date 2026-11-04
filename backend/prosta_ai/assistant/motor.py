"""Motor de coincidencia del asistente de uso (CU06).

Determinista y sin red: normaliza la pregunta, la compara con las frases de
cada tema de la base de conocimiento y devuelve la respuesta fija del tema que
mejor coincide. Antes de eso, un filtro clínico rechaza cualquier pregunta
sobre salud (RF-22). No se genera texto.
"""
import math
import re
import unicodedata
from difflib import get_close_matches

from prosta_ai.constantes import AVISO_EXPERIMENTAL

from . import contexto as ctx_mod
from .conocimiento import POR_ID, SUGERENCIAS_BASE, TEMAS, Tema
from .contexto import ContextoUsuario

UMBRAL = 2.2           # puntaje mínimo para aceptar un tema
EMPATE = 0.03          # diferencia relativa por debajo de la cual se considera empate

STOPWORDS = frozenset("""
a al algo ante con contra de del desde el ella ellos en entre es esta estan este esto estos
fue ha han hay la las le les lo los me mi mis muy o para pero por porque que se si sobre su sus
te tu tus un una uno unos unas y ya yo ser son soy somos eres puedo puedes puede pueden quiero
quisiera necesito tengo tienes tiene hago esa ese eso cual cuales como cuando donde quien pasa
pasan pues entonces favor dime oye
""".split())

SINONIMOS = {
    # cargar
    "subir": "cargar", "subo": "cargar", "suba": "cargar", "subes": "cargar", "sube": "cargar",
    "subimos": "cargar", "subirlo": "cargar", "importar": "cargar", "importo": "cargar",
    "adjuntar": "cargar", "adjunto": "cargar", "cargue": "cargar", "carguen": "cargar", "anadir": "cargar",
    "agregar": "cargar", "agrego": "cargar", "enviar": "cargar", "mandar": "cargar", "meter": "cargar",
    # errores
    "fallo": "error", "falla": "error", "fallar": "error", "fallan": "error", "fallado": "error",
    "fallida": "error", "fallidos": "error", "errores": "error", "falle": "error",
    "problema": "error", "problemas": "error", "bug": "error", "rechaza": "rechazo", "rechazado": "rechazo",
    "rechazada": "rechazo", "rechazar": "rechazo", "rechazan": "rechazo", "rechazo": "rechazo",
    "colgo": "error", "cayo": "error",
    # tiempo
    "tarda": "tiempo", "tardar": "tiempo", "tardan": "tiempo", "tardo": "tiempo", "demora": "tiempo",
    "demorar": "tiempo", "demoran": "tiempo", "lento": "tiempo", "lenta": "tiempo", "minutos": "tiempo",
    "segundos": "tiempo", "duracion": "tiempo", "dura": "tiempo", "tiempos": "tiempo",
    "rapido": "tiempo", "velocidad": "tiempo",
    # eliminar
    "borrar": "eliminar", "borro": "eliminar", "borra": "eliminar", "elimino": "eliminar",
    "quitar": "eliminar", "quito": "eliminar", "suprimir": "eliminar", "borre": "eliminar",
    # ver
    "veo": "ver", "mirar": "ver", "miro": "ver", "mostrar": "ver", "muestra": "ver", "visualizo": "ver",
    "visualizar": "ver", "consultar": "ver", "consulto": "ver", "encuentro": "ver", "aparece": "ver",
    # salir
    "salir": "cerrar", "salgo": "cerrar", "salida": "cerrar", "desconectar": "cerrar",
    # acceso
    "ingresar": "acceder", "ingreso": "acceder", "entrar": "acceder", "entro": "acceder",
    "accedo": "acceder", "acceso": "acceder", "clave": "contrasena", "password": "contrasena",
    # calidad / modelo
    "confiable": "confiable", "fiable": "confiable", "bueno": "confiable", "buena": "confiable",
    "preciso": "confiable", "precisa": "confiable", "exacto": "confiable", "exacta": "confiable",
    "precision": "confiable", "confianza": "confiable", "confiar": "confiable", "perfecta": "confiable",
    "perfecto": "confiable", "validada": "confiable", "validez": "confiable", "calidad": "confiable",
    # tamaño
    "pesa": "tamano", "peso": "tamano", "grande": "tamano", "pesado": "tamano", "megas": "tamano",
    "mb": "tamano", "megabytes": "tamano", "gb": "tamano",
    # varios
    "imagenes": "imagen", "fotos": "imagen", "foto": "imagen", "examen": "estudio", "examenes": "estudio",
    "ayuda": "ayuda", "ayudame": "ayuda", "ayudar": "ayuda", "ayudas": "ayuda",
    "usar": "usar", "uso": "usar", "utilizar": "usar", "utilizo": "usar", "usan": "usar", "usa": "usar",
    "usas": "usar", "usarlo": "usar",
    "ia": "ia", "inteligencia": "ia", "artificial": "ia",
    "nifti": "nifti", "niigz": "nifti", "dicom": "dicom",
    "comparar": "comparar", "comparo": "comparar", "compara": "comparar", "contrasto": "comparar",
    "contrastar": "comparar", "diferencia": "comparar",
    "transparencia": "opacidad", "translucido": "opacidad",
    "ocultar": "ocultar", "oculto": "ocultar", "esconder": "ocultar", "desactivar": "ocultar",
    "desactivo": "ocultar", "apagar": "ocultar", "quitarla": "ocultar",
    "bajar": "descargar", "bajo": "descargar", "descargo": "descargar", "guardar": "descargar",
    "guardo": "descargar", "exporto": "exportar", "sacar": "descargar", "saco": "descargar",
    "consigo": "descargar", "conseguir": "descargar",
    "hello": "hola", "ola": "hola", "buenas": "hola", "saludos": "hola", "hey": "hola",
    "chau": "adios", "chao": "adios", "bye": "adios",
    "gracia": "gracias", "grax": "gracias", "thanks": "gracias",
    "empiezo": "empezar", "comienzo": "empezar", "comenzar": "empezar", "arranco": "empezar",
    "iniciar": "empezar", "inicio": "empezar",
    "limite": "limitacion", "limites": "limitacion", "limitaciones": "limitacion",
}

SUFIJOS = (
    "amientos", "imientos", "amiento", "imiento", "aciones", "uciones", "iciones", "acion", "ucion", "icion",
    "adores", "ador", "idades", "idad", "mente", "ables", "able", "ibles", "ible", "ando", "iendo",
    "aron", "ieron", "ados", "adas", "idos", "idas", "ado", "ada", "ido", "ida", "ante", "ar", "er", "ir",
    "an", "en", "as", "es", "os", "s",
)

RUTAS_TEMA_SALUDO = {"saludo", "gracias", "despedida"}


# ------------------------------------------------------------------ texto
def normalizar(texto: str) -> str:
    """Minúsculas, sin tildes ni signos; solo letras, números y espacios."""
    sin_tildes = "".join(
        c for c in unicodedata.normalize("NFD", texto.lower()) if unicodedata.category(c) != "Mn"
    )
    return re.sub(r"[^a-z0-9]+", " ", sin_tildes).strip()


def raiz(palabra: str) -> str:
    """Raíz aproximada de una palabra ya normalizada (plurales, verbos y sufijos comunes)."""
    if len(palabra) <= 3 or palabra.isdigit():
        return palabra
    for sufijo in SUFIJOS:
        if palabra.endswith(sufijo) and len(palabra) - len(sufijo) >= 3:
            palabra = palabra[: -len(sufijo)]
            break
    while len(palabra) > 3 and palabra[-1] in "aeiou":
        palabra = palabra[:-1]
    return palabra


def _palabras(texto_normalizado: str) -> list[str]:
    return [SINONIMOS.get(p, p) for p in texto_normalizado.split()]


def _tokens_de(frase: str) -> list[str]:
    return [raiz(p) for p in _palabras(normalizar(frase)) if p not in STOPWORDS]


# ------------------------------------------------------------------ filtro clínico
_FUERTE = re.compile(
    r"\b(cancer\w*|tumor\w*|carcinoma\w*|diagnos\w*|tratamient\w*|tratarme|tratarse|sintoma\w*|enferm\w*|"
    r"pronostic\w*|biopsi\w*|psa|antigeno\w*|cirug\w*|operarme|operarse|operacion|terapia\w*|quimio\w*|"
    r"radioterapia|medicament\w*|medicacion|medicina\w*|medico\w*|doctor\w*|receta\w*|dosis|dolor\w*|"
    r"duele\w*|lesion\w*|metastas\w*|malign\w*|benign\w*|urolog\w*|oncolog\w*|gleason|pirads|hiperplasia|"
    r"prostatitis|infeccion\w*|nodulo\w*|quiste\w*|anormal\w*|patolog\w*|sangre|sangrado|orina\w*|"
    r"erecti\w*|impoten\w*|curar\w*|curable|riesgo\w*|peligros\w*|morir\w*|muerte|hallazgo\w*|"
    r"anomalia\w*|sospech\w*|alteracion\w*|bulto|metastasis|sano|sana|saludable|enfermo|"
    r"asusta\w*|preocup\w*|angusti\w*|miedo)\b"
)

_PERSONAL = [
    # familiares y terceros
    re.compile(r"\b(mi|mis|su|sus|un|una)\s+(papa|padre|madre|mama|abuel\w+|espos\w+|herman\w+|hij\w+|tio|tia|"
               r"familiar\w*|familia|amig\w+|pareja|marido|suegr\w+|cunad\w+|prim\w+|novi\w+|vecin\w+|"
               r"pacient\w*|conocid\w+)\b"),
    # partes del cuerpo o salud propias
    re.compile(r"\b(mi|mis|su|sus)\s+(\w+\s+)?(prostata|cuerpo|salud|organo\w*|vejiga|riñon\w*|analisis)\b"),
    re.compile(r"\b(la|el)\s+(salud)\s+de\b"),
    # estado de salud
    re.compile(r"\b(estoy|estamos|esta|estas|me\s+siento)\s+(muy\s+|algo\s+)?(mal|grave|bien\s+de\s+salud|sano|sana)\b"),
    re.compile(r"\b(tengo|tiene|tenga|tenemos|padezco|sufro|sufre|hay)\s+(un\s+|algun\s+)?"
               r"(algo\s+(malo|grave|raro|mal|anormal)|problema\w*\s+(de|en|con)\s+(la\s+|mi\s+)?(prostata|salud|vejiga))\b"),
    re.compile(r"\b(debo|debemos|deberia|tengo\s+que|hay\s+que)\s+(ir\s+al|consultar|operar\w*|tomar|hacerme|someterme)\b"),
    re.compile(r"\b(saber|ver|detectar|descartar|confirmar|averiguar|comprobar|revisar)\s+si\s+"
               r"(tengo|tiene|hay|estoy|esta|padezco)\b"),
    re.compile(r"\b(para|puede|sirve\s+para)\s+(detectar|descartar|confirmar|prevenir)\b"),
    re.compile(r"\b(cuanto|cuanta)\s+(tiempo\s+)?(me\s+queda|de\s+vida)\b|\bexpectativa\s+de\s+vida\b|\besperanza\s+de\s+vida\b"),
    re.compile(r"\bresultado\s+(es\s+|salio\s+|sale\s+|dio\s+)?(positivo|negativo)\b"),
    re.compile(r"\b(mi|mis)\s+(prostata|salud)\b"),
]

# Se omiten si la pregunta trata de Dice, IoU o métricas (ahí «resultado» es el valor de la métrica)
_CONTEXTUAL = [
    re.compile(r"\b(es|seria|sera|esta)\s+(muy\s+)?(grave|malo|mala|serio|seria|peligroso|preocupante)\b"),
    re.compile(r"\bque\s+tan\s+(grave|malo|mal|serio|peligroso|avanzado)\b"),
    re.compile(r"\b(normal|anormal|sano|sana|saludable)\b.*\b(resultado|resonancia|prostata|examen|imagen|corte)\b"),
    re.compile(r"\b(resultado|resonancia|prostata|examen|imagen)\b.*\b(normal|anormal|sano|sana|saludable)\b"),
    re.compile(r"\b(interpret\w*|analiz\w*|evalu\w*|examin\w*|lee|leer|explic\w*|dime\s+que\s+tengo)\s+"
               r"(mi\s+|esta\s+|la\s+|una\s+|esa\s+|este\s+|mis\s+)?(resonancia\w*|imagen\w*|prostata|examen\w*)\b"),
    re.compile(r"\b(mi|mis)\s+(resonancia\w*|examen\w*|imagen\w*|resultado\w*)\s+(esta|salio|sale|tiene|muestra|indica|"
               r"dice|significa|se\s+ve|es|son|estan)\b"),
    re.compile(r"\bque\s+(dice|significa|quiere\s+decir|indica|muestra)\s+(mi|mis)\s+(resonancia\w*|examen\w*|imagen\w*|resultado\w*)\b"),
    re.compile(r"\b(buen|mal|mala|buena)\s+(resultado|signo|noticia|sena\w*)\b"),
    re.compile(r"\b(esta|estan)\s+(bien|mal)\s+(mi|mis|la|el|los)\s+(prostata|resonancia|examen|imagen|resultado)\w*"),
]
_METRICAS = re.compile(r"\b(dice|iou|metrica\w*|jaccard|roi|segmentacion|opacidad|zoom|corte\w*)\b")


def es_clinica(pregunta: str) -> bool:
    """True si la pregunta pide algo de salud o interpretación clínica."""
    texto = normalizar(pregunta).replace("dispositivo medico", "dispositivo")
    if _FUERTE.search(texto) or any(p.search(texto) for p in _PERSONAL):
        return True
    if _METRICAS.search(texto):
        return False
    return any(p.search(texto) for p in _CONTEXTUAL)


# ------------------------------------------------------------------ índice de temas
def _construir_indice():
    frases_por_tema: dict[str, list[tuple[list[str], float]]] = {}
    df: dict[str, int] = {}
    conocidas: dict[str, str] = {}
    for tema in TEMAS:
        frases = []
        vistos: set[str] = set()
        for f in tema.frases:
            texto, peso = f if isinstance(f, tuple) else (f, 1.0)
            tokens = _tokens_de(texto)
            if not tokens:
                continue
            frases.append((tokens, peso))
            vistos.update(tokens)
            for p in _palabras(normalizar(texto)):
                if p not in STOPWORDS:
                    conocidas[p] = raiz(p)
        frases_por_tema[tema.id] = frases
        for t in vistos:
            df[t] = df.get(t, 0) + 1
    n = len(TEMAS)
    idf = {t: math.log(1 + n / c) for t, c in df.items()}
    return frases_por_tema, idf, conocidas


_FRASES, _IDF, _CONOCIDAS = _construir_indice()
_VOCABULARIO = list(_CONOCIDAS)


def _tokens_pregunta(texto: str) -> set[str]:
    """Raíces de la pregunta; las palabras desconocidas se corrigen si se parecen a una conocida."""
    salida = set()
    for p in _palabras(texto):
        if p in STOPWORDS:
            continue
        if p not in _CONOCIDAS and len(p) >= 4:
            cerca = get_close_matches(p, _VOCABULARIO, n=1, cutoff=0.82)
            if cerca:
                p = cerca[0]
        salida.add(_CONOCIDAS.get(p, raiz(p)))
    return salida


def _puntaje(tema_id: str, tokens: set[str]) -> float:
    valores = []
    for frase, peso in _FRASES[tema_id]:
        coinciden = [t for t in frase if t in tokens]
        if not coinciden:
            continue
        suma = sum(_IDF[t] for t in coinciden)
        total = sum(_IDF[t] for t in frase)
        cobertura = suma / total
        valor = peso * suma * cobertura
        if cobertura == 1 and len(frase) >= 2:
            valor *= 1.4  # coincidencia completa de una frase de varias palabras
        valores.append(valor)
    if not valores:
        return 0.0
    valores.sort(reverse=True)
    return valores[0] + 0.25 * sum(valores[1:4])


def clasificar(pregunta: str) -> list[tuple[str, float]]:
    """Temas ordenados por puntaje (de mayor a menor), solo los que puntúan."""
    tokens = _tokens_pregunta(normalizar(pregunta))
    puntajes = [(t.id, _puntaje(t.id, tokens)) for t in TEMAS]
    return sorted((p for p in puntajes if p[1] > 0), key=lambda p: -p[1])


# ------------------------------------------------------------------ respuestas
def texto_plano(intro: str, pasos: list[str], nota: str | None) -> str:
    partes = [intro]
    partes += [f"{i}. {p}" for i, p in enumerate(pasos, 1)]
    if nota:
        partes.append("\n" + nota)
    return "\n".join(partes)


def _armar(tema: str, intro: str, pasos: list[str], nota: str | None, enlace: dict | None,
           sugerencias: list[str], extra: str = "") -> dict:
    return {
        "tema": tema,
        "respuesta": texto_plano(intro, pasos, nota) + extra,
        "intro": intro,
        "pasos": pasos,
        "nota": nota,
        "enlace": enlace,
        "sugerencias": sugerencias[:3],
        "aviso": AVISO_EXPERIMENTAL,
    }


def _lista_sugerencias(sugerencias: list[str]) -> str:
    return "\n\nPuedes preguntarme, por ejemplo:\n" + "\n".join(f"- {s}" for s in sugerencias)


def respuesta_clinica() -> dict:
    sugerencias = [POR_ID[i].sugerencia for i in ("primeros_pasos", "comparar_roi", "metricas")]
    return _armar(
        "clinico",
        "No puedo ayudarte con eso: no doy orientación de salud, no interpreto imágenes ni resultados "
        "médicos y no tomo decisiones clínicas. Prosta-AI no diagnostica.",
        [],
        "Si te preocupa tu salud o la de alguien cercano, consulta a un profesional de la salud. "
        "Con gusto te ayudo con el uso de la aplicación.",
        None, sugerencias, _lista_sugerencias(sugerencias),
    )


def respuesta_no_entendido(candidatos: list[str]) -> dict:
    sugerencias = [POR_ID[i].sugerencia for i in candidatos if i not in RUTAS_TEMA_SALUDO][:3]
    for s in SUGERENCIAS_BASE:
        if len(sugerencias) >= 3:
            break
        if s not in sugerencias:
            sugerencias.append(s)
    sugerencias = sugerencias[:3]
    return _armar(
        "no_entendido",
        "No estoy seguro de haber entendido tu pregunta. Solo puedo orientarte sobre el uso de Prosta-AI: "
        "cargar archivos, procesar, ver la ROI y sus límites.",
        [], "Prueba a reformularla o elige una de estas preguntas.",
        None, sugerencias, _lista_sugerencias(sugerencias),
    )


def _de_tema(tema: Tema) -> dict:
    return _armar(
        tema.id, tema.intro, list(tema.pasos), tema.nota, tema.enlace,
        [POR_ID[i].sugerencia for i in tema.relacionados],
    )


def responder(pregunta: str, contexto: ContextoUsuario | None = None) -> dict:
    """Respuesta fija a una pregunta de uso. Ver el contrato en `docs-tecnicos/especificacion-tecnica.md`."""
    if es_clinica(pregunta):
        return respuesta_clinica()

    if contexto is not None:
        intencion = ctx_mod.detectar(set(normalizar(pregunta).split()))
        if intencion:
            datos = ctx_mod.responder_contexto(intencion, contexto)
            if datos:
                return _armar(datos["tema"], datos["intro"], datos["pasos"], datos["nota"],
                              datos["enlace"], datos["sugerencias"])

    ranking = clasificar(pregunta)
    if not ranking or ranking[0][1] < UMBRAL:
        return respuesta_no_entendido([t for t, _ in ranking[:3]])
    if len(ranking) > 1:
        (mejor_id, mejor), (_, segundo) = ranking[0], ranking[1]
        # Empate exacto entre temas distintos: mejor pedir una aclaración
        if segundo >= UMBRAL and (mejor - segundo) / mejor < EMPATE and mejor_id not in RUTAS_TEMA_SALUDO:
            return respuesta_no_entendido([t for t, _ in ranking[:3]])
    return _de_tema(POR_ID[ranking[0][0]])
