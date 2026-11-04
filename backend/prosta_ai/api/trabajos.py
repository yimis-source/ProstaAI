"""CU03 y CU04: estado del trabajo, resultado, cortes en PNG y exportación."""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from prosta_ai.api import rendering
from prosta_ai.api.deps import get_db, get_storage, usuario_actual
from prosta_ai.constantes import AVISO_EXPERIMENTAL, COMPLETADO, PENDIENTE
from prosta_ai.models import Estudio, Trabajo, Usuario
from prosta_ai.pipeline.stages import STAGES
from prosta_ai.repositories import JobRepository, ResultRepository
from prosta_ai.storage import PrivateStorage

router = APIRouter(prefix="/trabajos", tags=["trabajos"])


def _iso(fecha):
    return fecha.isoformat() if fecha else None


def detalle_trabajo(db: Session, trabajo: Trabajo) -> dict:
    estudio = db.get(Estudio, trabajo.id_estudio)
    etapas = JobRepository(db).etapas(trabajo.id_trabajo)
    if etapas:
        lista = [
            {"nombre": e.nombre, "estado": e.estado,
             "duracion_s": None if e.duracion_s is None else float(e.duracion_s)}
            for e in etapas
        ]
    else:  # aún no tomado por el worker
        lista = [{"nombre": n, "estado": PENDIENTE, "duracion_s": None} for n in STAGES]
    return {
        "id": trabajo.id_trabajo,
        "id_estudio": trabajo.id_estudio,
        "codigo": estudio.codigo_anonimo,
        "estado": trabajo.estado,
        "etapa_fallida": trabajo.etapa_fallida,
        "mensaje_error": trabajo.mensaje_error,
        "fecha_creacion": _iso(trabajo.fecha_creacion),
        "fecha_inicio": _iso(trabajo.fecha_inicio),
        "fecha_fin": _iso(trabajo.fecha_fin),
        "etapas": lista,
    }


def _trabajo_o_404(db: Session, id_trabajo: int, usuario: Usuario) -> Trabajo:
    trabajo = JobRepository(db).obtener_de_usuario(id_trabajo, usuario)
    if trabajo is None:
        raise HTTPException(404, "Trabajo no encontrado.")
    return trabajo


def _volumen(db: Session, trabajo: Trabajo, storage: PrivateStorage):
    """Carga imagen y máscara del resultado; 404 si el trabajo no está completado."""
    resultado = ResultRepository(db).del_trabajo(trabajo.id_trabajo)
    if trabajo.estado != COMPLETADO or resultado is None:
        raise HTTPException(404, "El trabajo no tiene resultado disponible.")
    ruta_mascara = storage.absoluta(resultado.ruta_mascara)
    ruta_imagen = ruta_mascara.parent / "imagen.nii.gz"
    if not ruta_imagen.exists():
        raise HTTPException(404, "No se encontró la imagen del resultado.")
    try:
        return resultado, rendering.cargar_volumen(ruta_imagen, ruta_mascara)
    except ValueError:
        raise HTTPException(500, "El resultado almacenado no es consistente.")


@router.get("/{id_trabajo}")
def estado(id_trabajo: int, db: Session = Depends(get_db), usuario: Usuario = Depends(usuario_actual)):
    return detalle_trabajo(db, _trabajo_o_404(db, id_trabajo, usuario))


@router.get("/{id_trabajo}/resultado")
def resultado(
    id_trabajo: int, db: Session = Depends(get_db), storage: PrivateStorage = Depends(get_storage),
    usuario: Usuario = Depends(usuario_actual),
):
    trabajo = _trabajo_o_404(db, id_trabajo, usuario)
    res, vol = _volumen(db, trabajo, storage)
    return {
        "id_trabajo": trabajo.id_trabajo,
        "codigo": db.get(Estudio, trabajo.id_estudio).codigo_anonimo,
        "dice": None if res.dice is None else float(res.dice),
        "iou": None if res.iou is None else float(res.iou),
        "tiempo_total_s": None if res.tiempo_total_s is None else float(res.tiempo_total_s),
        "modelo": {"nombre": trabajo.modelo.nombre, "version": trabajo.modelo.version},
        "cortes": vol.cortes,
        "forma": list(vol.forma),
        "aviso": AVISO_EXPERIMENTAL,
    }


@router.get("/{id_trabajo}/corte/{indice}")
def corte(
    id_trabajo: int, indice: int, capa: str = Query("imagen", pattern="^(imagen|mascara)$"),
    db: Session = Depends(get_db), storage: PrivateStorage = Depends(get_storage),
    usuario: Usuario = Depends(usuario_actual),
):
    trabajo = _trabajo_o_404(db, id_trabajo, usuario)
    _, vol = _volumen(db, trabajo, storage)
    if not 0 <= indice < vol.cortes:
        raise HTTPException(422, f"El corte debe estar entre 0 y {vol.cortes - 1}.")
    if capa == "mascara":
        if vol.mascara is None:
            raise HTTPException(404, "El resultado no tiene máscara.")
        renderizador = rendering.MaskSliceRenderer()
    else:
        renderizador = rendering.ImageSliceRenderer()
    return Response(rendering.a_png(renderizador.render(vol, indice)), media_type="image/png")


@router.get("/{id_trabajo}/exportar")
def exportar(
    id_trabajo: int, db: Session = Depends(get_db), storage: PrivateStorage = Depends(get_storage),
    usuario: Usuario = Depends(usuario_actual),
):
    trabajo = _trabajo_o_404(db, id_trabajo, usuario)
    _, vol = _volumen(db, trabajo, storage)
    imagen = rendering.renderizador_exportacion().render(vol, vol.cortes // 2)
    cabeceras = {"Content-Disposition": f'attachment; filename="roi_{trabajo.id_trabajo}.png"'}
    return Response(rendering.a_png(imagen), media_type="image/png", headers=cabeceras)
