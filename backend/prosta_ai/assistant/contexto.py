"""Preguntas sobre los estudios del propio usuario (CU06).

Solo se informa de datos que la aplicación ya tiene (código anónimo, estado,
etapa fallida, mensaje de error, Dice e IoU) y de los pasos a seguir en la
interfaz. Nunca se interpreta el contenido de una imagen. Solo se consultan
los estudios del usuario que pregunta.
"""
from dataclasses import dataclass

from sqlalchemy.orm import Session

from prosta_ai.constantes import COMPLETADO, EN_PROCESO, FALLIDO, LISTO_PARA_PROCESAR, NO_COMPATIBLE, PENDIENTE
from prosta_ai.models import Estudio, Usuario
from prosta_ai.repositories import StudyRepository
from prosta_ai.repositories.studies import estado_visible

from .conocimiento import POR_ID, NOTA_ROI

NOTA_METRICA = (
    "Dice e IoU miden cuánto coincide la ROI con la máscara de referencia; no indican nada sobre la salud de nadie."
)

POSESIVOS = {"mi", "mis", "ultimo", "ultima", "ultimos", "ultimas", "reciente", "recientes"}
ESTUDIO = {"estudio", "estudios", "procesamiento", "trabajo", "carga", "archivo", "archivos"}
FALLO = {"fallo", "falla", "fallan", "fallado", "fallido", "fallida", "error", "errores", "rechazo",
         "rechazado", "rechazaron", "problema", "problemas", "detuvo", "detenido", "colgo"}
ESTADO = {"estado", "va", "termino", "terminado", "avance", "progreso", "paso", "pasa", "procesando",
          "listo", "listos", "pendiente", "completo", "completado", "finalizo"}
RESULTADO = {"resultado", "resultados", "dice", "iou", "metrica", "metricas"}
CONTEO = {"cuantos", "cuantas", "numero", "total"}


@dataclass
class ContextoUsuario:
    """Sesión de base de datos y usuario que pregunta."""
    db: Session
    usuario: Usuario


def _estudios(ctx: ContextoUsuario) -> list[Estudio]:
    # El repositorio filtra por usuario: nunca se ven estudios ajenos
    return StudyRepository(ctx.db).listar(ctx.usuario)


def _sugerencias(*ids: str) -> list[str]:
    return [POR_ID[i].sugerencia for i in ids]


def detectar(palabras: set[str]) -> str | None:
    """Devuelve la intención sobre los estudios propios o None si es una duda general."""
    tiene_estudio = bool(palabras & ESTUDIO)
    es_mio = bool(palabras & POSESIVOS)
    if palabras & CONTEO and "estudios" in palabras and palabras & {"tengo", "he", "hay", "llevo", "tenemos",
                                                                    "cargado", "cargados", "mis"}:
        return "conteo"
    if palabras & FALLO and es_mio and tiene_estudio:
        return "error"
    if palabras & FALLO and "me" in palabras and palabras & {"salio", "aparecio", "dio", "sale", "paso"}:
        return "error_suave"
    if palabras & RESULTADO and es_mio:
        return "resultado"
    if palabras & ESTADO and es_mio and tiene_estudio:
        return "estado"
    return None


def _formato_metrica(valor) -> str:
    return f"{float(valor):.3f}"


def _ultimo_trabajo(estudio: Estudio):
    return estudio.trabajos[-1] if estudio.trabajos else None


def _sin_estudios() -> dict:
    return {
        "tema": "ctx_sin_estudios",
        "intro": "Todavía no tienes estudios cargados en tu cuenta.",
        "pasos": [
            "Ve a «Cargar estudios» y sube los archivos de un estudio de prueba.",
            "Después pulsa «Procesar» en «Procesamiento» para obtener la ROI.",
        ],
        "nota": "Si no tienes archivos, puedo explicarte de dónde sacar datos de prueba públicos.",
        "enlace": {"ruta": "/cargar", "texto": "Ir a Cargar estudios"},
        "sugerencias": _sugerencias("datos_prueba", "formatos", "flujo"),
    }


def _detalle_fallo(estudio: Estudio) -> dict:
    trabajo = _ultimo_trabajo(estudio)
    codigo = estudio.codigo_anonimo
    if trabajo is None:  # no compatible
        return {
            "tema": "ctx_error",
            "intro": f"El estudio {codigo} fue rechazado al cargarlo (estado «No compatible»).",
            "pasos": [
                "Revisa que los archivos sean NIfTI (.nii o .nii.gz, uno solo) o DICOM (.dcm varios o un .zip), "
                "sin mezclar formatos y de menos de 500 MB.",
                "Carga de nuevo el estudio en «Cargar estudios». Puedes eliminar el rechazado desde «Mis estudios».",
            ],
            "nota": "Un estudio no compatible no se puede procesar.",
            "enlace": {"ruta": "/cargar", "texto": "Ir a Cargar estudios"},
            "sugerencias": _sugerencias("rechazo_carga", "formatos", "eliminar"),
        }
    etapa = trabajo.etapa_fallida or "desconocida"
    motivo = trabajo.mensaje_error or "sin detalle disponible"
    return {
        "tema": "ctx_error",
        "intro": f"Tu estudio {codigo} falló en la etapa «{etapa}».",
        "pasos": [
            f"Mensaje registrado: «{motivo}»",
            f"Ve a «Procesamiento», elige {codigo} y revisa el estado de cada etapa.",
            "Si el motivo es de los archivos (formato, cortes, referencia con otra forma), corrígelos y "
            "cárgalos de nuevo.",
            "Si el estudio es correcto, pulsa «Volver a procesar» para intentarlo otra vez.",
        ],
        "nota": "Si vuelve a fallar con el mismo mensaje, prueba con otro estudio de prueba.",
        "enlace": {"ruta": f"/procesamiento?estudio={estudio.id_estudio}", "texto": f"Abrir {codigo} en Procesamiento"},
        "sugerencias": _sugerencias("etapas", "rechazo_carga", "formatos"),
    }


def _error(ctx: ContextoUsuario, estricto: bool) -> dict | None:
    estudios = _estudios(ctx)
    if not estudios:
        return _sin_estudios() if estricto else None
    con_fallo = [e for e in estudios if estado_visible(e) in (FALLIDO, NO_COMPATIBLE)]
    if con_fallo:
        return _detalle_fallo(con_fallo[0])  # el más reciente
    if not estricto:
        return None
    ultimo = estudios[0]
    return {
        "tema": "ctx_error",
        "intro": f"No veo estudios con errores en tu cuenta. El último, {ultimo.codigo_anonimo}, está "
                 f"«{estado_visible(ultimo)}».",
        "pasos": [
            "Si el error apareció al cargar archivos, la app muestra el motivo en rojo y el estudio queda como «No compatible».",
            "Si fue durante el procesamiento, la pantalla «Procesamiento» indica la etapa y el motivo.",
        ],
        "nota": "Cuéntame qué mensaje viste y te digo qué revisar, sin datos personales.",
        "enlace": {"ruta": "/estudios", "texto": "Ir a Mis estudios"},
        "sugerencias": _sugerencias("error_proceso", "rechazo_carga", "mis_estudios"),
    }


def _estado(ctx: ContextoUsuario) -> dict:
    estudios = _estudios(ctx)
    if not estudios:
        return _sin_estudios()
    estudio = estudios[0]
    estado = estado_visible(estudio)
    codigo = estudio.codigo_anonimo
    trabajo = _ultimo_trabajo(estudio)
    if estado in (FALLIDO, NO_COMPATIBLE):
        return _detalle_fallo(estudio)
    intro = f"Tu último estudio es {codigo} ({estudio.formato}) y su estado es «{estado}»."
    if estado == LISTO_PARA_PROCESAR:
        pasos = ["Aún no lo has procesado.", "Ve a «Procesamiento», elígelo y pulsa «Procesar»."]
        enlace = {"ruta": f"/procesamiento?estudio={estudio.id_estudio}", "texto": "Ir a Procesamiento"}
    elif estado in (PENDIENTE, EN_PROCESO):
        en_curso = [e.nombre for e in trabajo.etapas if e.estado == EN_PROCESO]
        hechas = sum(1 for e in trabajo.etapas if e.estado == COMPLETADO)
        pasos = [f"Lleva {hechas} de 5 etapas completadas."]
        if en_curso:
            pasos.append(f"Ahora está en la etapa «{en_curso[0]}».")
        pasos.append("La pantalla «Procesamiento» se actualiza sola cada 1,5 segundos.")
        enlace = {"ruta": f"/procesamiento?estudio={estudio.id_estudio}", "texto": "Ir a Procesamiento"}
    else:  # completado
        pasos = ["Las cinco etapas terminaron.", "Pulsa el botón para comparar la ROI con la imagen original."]
        enlace = {"ruta": f"/roi?trabajo={trabajo.id_trabajo}", "texto": f"Ver ROI de {codigo}"}
    return {
        "tema": "ctx_estado", "intro": intro, "pasos": pasos, "nota": NOTA_ROI if estado == COMPLETADO else None,
        "enlace": enlace, "sugerencias": _sugerencias("etapas", "tiempos", "mis_estudios"),
    }


def _conteo(ctx: ContextoUsuario) -> dict:
    estudios = _estudios(ctx)
    if not estudios:
        return _sin_estudios()
    por_estado: dict[str, int] = {}
    for e in estudios:
        por_estado[estado_visible(e)] = por_estado.get(estado_visible(e), 0) + 1
    n = len(estudios)
    return {
        "tema": "ctx_conteo",
        "intro": f"Tienes {n} {'estudio' if n == 1 else 'estudios'} en tu cuenta:",
        "pasos": [f"{estado.capitalize()}: {cantidad}" for estado, cantidad in sorted(por_estado.items())],
        "nota": "Puedes verlos, filtrarlos y eliminarlos en «Mis estudios».",
        "enlace": {"ruta": "/estudios", "texto": "Ir a Mis estudios"},
        "sugerencias": _sugerencias("mis_estudios", "eliminar", "procesar"),
    }


def _resultado(ctx: ContextoUsuario) -> dict:
    estudios = _estudios(ctx)
    if not estudios:
        return _sin_estudios()
    for e in estudios:
        trabajo = _ultimo_trabajo(e)
        if trabajo is not None and trabajo.estado == COMPLETADO and trabajo.resultado is not None:
            r = trabajo.resultado
            if r.dice is None:
                pasos = ["No tiene máscara de referencia, así que Dice e IoU no están disponibles."]
            else:
                pasos = [
                    f"Dice: {_formato_metrica(r.dice)}",
                    f"IoU: {_formato_metrica(r.iou)}",
                    "Cuanto más cerca de 1, mayor coincidencia entre la ROI y la referencia.",
                ]
            if r.tiempo_total_s is not None:
                pasos.append(f"Tiempo total de procesamiento: {float(r.tiempo_total_s):.1f} s")
            return {
                "tema": "ctx_resultado",
                "intro": f"Tu último resultado es el del estudio {e.codigo_anonimo}:",
                "pasos": pasos,
                "nota": NOTA_METRICA,
                "enlace": {"ruta": f"/roi?trabajo={trabajo.id_trabajo}", "texto": f"Ver ROI de {e.codigo_anonimo}"},
                "sugerencias": _sugerencias("interpretar_dice", "comparar_roi", "exportar"),
            }
    return {
        "tema": "ctx_resultado",
        "intro": "Todavía no tienes estudios con resultado.",
        "pasos": ["Procesa un estudio en «Procesamiento»; cuando termine podrás verlo en «Visualizar ROI»."],
        "nota": None,
        "enlace": {"ruta": "/procesamiento", "texto": "Ir a Procesamiento"},
        "sugerencias": _sugerencias("procesar", "etapas", "ver_resultados"),
    }


def responder_contexto(intencion: str, ctx: ContextoUsuario) -> dict | None:
    """Respuesta con datos del usuario, o None si no hay nada concreto que decir."""
    if intencion == "error":
        return _error(ctx, estricto=True)
    if intencion == "error_suave":
        return _error(ctx, estricto=False)
    if intencion == "estado":
        return _estado(ctx)
    if intencion == "conteo":
        return _conteo(ctx)
    if intencion == "resultado":
        return _resultado(ctx)
    return None
