"""CU02, CU03 y CU05: carga, consulta, borrado y solicitud de procesamiento."""
import logging

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from fastapi.responses import Response
from sqlalchemy.orm import Session

from prosta_ai.api.admision import crear_info
from prosta_ai.api.deps import get_db, get_storage, id_modelo_activo, usuario_actual
from prosta_ai.api.trabajos import detalle_trabajo
from prosta_ai.constantes import ADMITIDO, EN_PROCESO, NO_COMPATIBLE, PENDIENTE
from prosta_ai.models import Estudio, Usuario
from prosta_ai.pipeline.errors import AdmissionError
from prosta_ai.repositories import JobRepository, StudyRepository
from prosta_ai.repositories.studies import estado_visible
from prosta_ai.storage import PrivateStorage

log = logging.getLogger(__name__)
router = APIRouter(prefix="/estudios", tags=["estudios"])


def _num(valor):
    return None if valor is None else float(valor)


def _ultimo_resultado(estudio: Estudio):
    return estudio.trabajos[-1].resultado if estudio.trabajos else None


def _resumen(estudio: Estudio) -> dict:
    ultimo = estudio.trabajos[-1] if estudio.trabajos else None
    resultado = _ultimo_resultado(estudio)
    return {
        "id": estudio.id_estudio,
        "codigo": estudio.codigo_anonimo,
        "formato": estudio.formato,
        "fecha_carga": estudio.fecha_carga.isoformat(),
        "estado": estado_visible(estudio),
        "id_ultimo_trabajo": ultimo.id_trabajo if ultimo else None,
        "dice": _num(resultado.dice) if resultado else None,
        "iou": _num(resultado.iou) if resultado else None,
    }


def _obtener_o_404(db: Session, id_estudio: int, usuario: Usuario) -> Estudio:
    estudio = StudyRepository(db).obtener(id_estudio, usuario)
    if estudio is None:
        raise HTTPException(404, "Estudio no encontrado.")
    return estudio


def _formato_probable(nombres: list[str]) -> str:
    """Formato aproximado para registrar un rechazo (la admisión no lo devolvió)."""
    for n in nombres:
        if n.lower().endswith((".dcm", ".zip")):
            return "DICOM"
    return "NIfTI"


async def _info(archivos: list[UploadFile]) -> list:
    lista = []
    for f in archivos:
        cabecera = await f.read(512)
        await f.seek(0)
        tamano = f.size if f.size is not None else 0
        lista.append(crear_info(f.filename or "", tamano, cabecera))
    return lista


@router.get("")
def listar(db: Session = Depends(get_db), usuario: Usuario = Depends(usuario_actual)):
    return [_resumen(e) for e in StudyRepository(db).listar(usuario)]


@router.post("", status_code=201)
async def cargar(
    request: Request,
    archivos: list[UploadFile] = File(default=[]),
    referencia: list[UploadFile] = File(default=[]),
    db: Session = Depends(get_db),
    storage: PrivateStorage = Depends(get_storage),
    usuario: Usuario = Depends(usuario_actual),
):
    # Los campos vacíos que envía el navegador sin archivo se descartan
    archivos = [f for f in archivos if f.filename]
    referencia = [f for f in referencia if f.filename]
    if not archivos:
        raise HTTPException(422, "Seleccione al menos un archivo de imagen.")

    app = request.app
    admitir = app.state.admission
    max_bytes = app.state.settings.max_upload_bytes
    repo = StudyRepository(db)

    # Admisión (formato y tamaño) antes de guardar nada
    try:
        formato = admitir(await _info(archivos), max_bytes)
        if referencia:
            admitir(await _info(referencia), max_bytes)
    except AdmissionError as exc:
        nombres = [f.filename or "" for f in archivos]
        repo.crear(usuario, _formato_probable(nombres), NO_COMPATIBLE)
        raise HTTPException(422, exc.message)

    estudio = repo.crear(usuario, formato, ADMITIDO)
    try:
        for tipo, grupo in (("imagen", archivos), ("referencia", referencia)):
            for n, f in enumerate(grupo, start=1):
                ruta, tamano, sha = storage.guardar_archivo(
                    estudio.codigo_anonimo, tipo, n, f.filename or "", f.file
                )
                repo.agregar_archivo(estudio.id_estudio, ruta, tamano, sha)
        db.commit()
    except Exception:
        log.exception("No se pudo guardar el estudio %s", estudio.codigo_anonimo)
        db.rollback()
        storage.borrar_estudio(estudio.codigo_anonimo)
        repo.eliminar(estudio)
        raise HTTPException(500, "No se pudo guardar el estudio. Intente de nuevo.")
    return {
        "id": estudio.id_estudio, "codigo": estudio.codigo_anonimo,
        "formato": estudio.formato, "estado": estado_visible(estudio),
    }


@router.get("/{id_estudio}")
def detalle(id_estudio: int, db: Session = Depends(get_db), usuario: Usuario = Depends(usuario_actual)):
    estudio = _obtener_o_404(db, id_estudio, usuario)
    datos = _resumen(estudio)
    datos["estado_admision"] = estudio.estado_admision
    datos["trabajos"] = [detalle_trabajo(db, t) for t in estudio.trabajos]
    return datos


@router.delete("/{id_estudio}", status_code=204)
def eliminar(
    id_estudio: int, db: Session = Depends(get_db),
    storage: PrivateStorage = Depends(get_storage), usuario: Usuario = Depends(usuario_actual),
):
    estudio = _obtener_o_404(db, id_estudio, usuario)
    if any(t.estado == EN_PROCESO for t in estudio.trabajos):
        raise HTTPException(409, "El estudio se está procesando; espere a que termine.")
    codigo, ids = estudio.codigo_anonimo, [t.id_trabajo for t in estudio.trabajos]
    StudyRepository(db).eliminar(estudio)
    storage.borrar_estudio(codigo)
    for id_trabajo in ids:
        storage.borrar_resultado(id_trabajo)
    return Response(status_code=204)


@router.post("/{id_estudio}/procesar", status_code=201)
def procesar(
    id_estudio: int, db: Session = Depends(get_db), usuario: Usuario = Depends(usuario_actual),
    id_modelo: int = Depends(id_modelo_activo),
):
    estudio = _obtener_o_404(db, id_estudio, usuario)
    if estudio.estado_admision == NO_COMPATIBLE:
        raise HTTPException(409, "El estudio no es compatible y no se puede procesar.")
    jobs = JobRepository(db)
    if jobs.activo_del_estudio(estudio.id_estudio) is not None:
        raise HTTPException(409, "El estudio ya tiene un procesamiento pendiente o en curso.")
    trabajo = jobs.crear(estudio.id_estudio, id_modelo)
    return detalle_trabajo(db, trabajo)
