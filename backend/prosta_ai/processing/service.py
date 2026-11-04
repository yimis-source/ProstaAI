"""ProcessingService (Facade): ejecuta un trabajo y deja su estado en la base de datos."""
import logging
import os
import time
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path
from typing import Any, Callable

from sqlalchemy.orm import Session, sessionmaker

from prosta_ai.constantes import (
    COMPLETADO, EN_PROCESO, FALLIDO, MENSAJE_ERROR_GENERICO, PENDIENTE,
)
from prosta_ai.db import ahora
from prosta_ai.jobs.state import Job
from prosta_ai.models import Estudio, EtapaTrabajo, Trabajo
from prosta_ai.pipeline.errors import StageError
from prosta_ai.pipeline.stages import SEGMENTACION, STAGES
from prosta_ai.repositories import JobRepository, ResultRepository
from prosta_ai.storage import PrivateStorage

log = logging.getLogger(__name__)

MENSAJE_INTERRUMPIDO = "El procesamiento se interrumpió. Vuelva a pulsar «Procesar»."
MENSAJE_MODELO = "No se pudo cargar el modelo de segmentación."


# --- Respaldo local de las interfaces del pipeline (misma forma que el contrato) ---
@dataclass
class _Entrada:
    files: list[Path]
    fmt: str
    reference_files: list[Path]
    output_dir: Path


@dataclass
class _Progreso:
    observers: list = field(default_factory=list)

    def attach(self, obs) -> None:
        self.observers.append(obs)

    def notify_start(self, stage: str) -> None:
        for o in self.observers:
            o.on_stage_start(stage)

    def notify_end(self, stage: str, duration_s: float) -> None:
        for o in self.observers:
            o.on_stage_end(stage, duration_s)

    def notify_failed(self, stage: str, message: str) -> None:
        for o in self.observers:
            o.on_stage_failed(stage, message)


def _crear_entrada(**datos) -> Any:
    try:
        from prosta_ai.pipeline.base import PipelineInput
    except ImportError:
        return _Entrada(**datos)
    return PipelineInput(**datos)


def _crear_progreso() -> Any:
    try:
        from prosta_ai.pipeline.progress import PipelineProgress
    except ImportError:
        return _Progreso()
    return PipelineProgress()


def pipeline_por_defecto(settings) -> Callable[[], Any]:
    """Devuelve un proveedor que construye el pipeline real la primera vez y luego lo reutiliza,
    para que los pesos del modelo se lean del disco una sola vez."""
    construido = []

    def proveedor():
        if not construido:
            from prosta_ai.pipeline.factory import build_pipeline

            construido.append(build_pipeline(settings.modelo_nombre, settings.modelo_dir))
        return construido[0]

    return proveedor


class DatabaseRecorder:
    """Observer: refleja el avance de cada etapa en etapa_trabajo."""

    def __init__(self, session_factory: sessionmaker[Session], id_trabajo: int):
        self._sf = session_factory
        self._id = id_trabajo

    def _etapa(self, s: Session, nombre: str) -> EtapaTrabajo | None:
        return next(
            (e for e in JobRepository(s).etapas(self._id) if e.nombre == nombre), None
        )

    def on_stage_start(self, stage: str) -> None:
        with self._sf() as s:
            etapa = self._etapa(s, stage)
            if etapa:
                etapa.estado, etapa.fecha_inicio = EN_PROCESO, ahora()
                s.commit()

    def on_stage_end(self, stage: str, duration_s: float) -> None:
        with self._sf() as s:
            etapa = self._etapa(s, stage)
            if etapa:
                etapa.estado, etapa.fecha_fin = COMPLETADO, ahora()
                etapa.duracion_s = Decimal(str(round(duration_s, 2)))
                s.commit()

    def on_stage_failed(self, stage: str, message: str) -> None:
        with self._sf() as s:
            etapa = self._etapa(s, stage)
            if etapa:
                etapa.estado, etapa.fecha_fin = FALLIDO, ahora()
                s.commit()


class ProcessingService:
    def __init__(
        self, session_factory: sessionmaker[Session], storage: PrivateStorage,
        pipeline_provider: Callable[[], Any],
    ):
        self._sf = session_factory
        self._storage = storage
        self._provider = pipeline_provider

    # --- toma del trabajo ---
    def iniciar_siguiente(self) -> int | None:
        """Pasa el siguiente pendiente a «en proceso» y crea sus 5 etapas."""
        with self._sf() as s:
            repo = JobRepository(s)
            fila = repo.reclamar_siguiente_pendiente()
            if fila is None:
                return None
            job = Job(fila.estado)
            job.iniciar()
            fila.estado, fila.fecha_inicio = job.estado, ahora()
            repo.crear_etapas(fila.id_trabajo, STAGES)
            s.commit()
            return fila.id_trabajo

    def ejecutar_siguiente(self) -> bool:
        id_trabajo = self.iniciar_siguiente()
        if id_trabajo is None:
            return False
        self.ejecutar(id_trabajo)
        return True

    def recuperar_interrumpidos(self) -> int:
        """Marca como fallidos los trabajos que quedaron «en proceso» tras un cierre."""
        with self._sf() as s:
            ids = [t.id_trabajo for t in JobRepository(s).en_proceso()]
        for id_trabajo in ids:
            self._fallar(id_trabajo, None, MENSAJE_INTERRUMPIDO)
        return len(ids)

    # --- ejecución ---
    def ejecutar(self, id_trabajo: int) -> None:
        try:
            entrada = self._preparar_entrada(id_trabajo)
            try:
                pipeline = self._provider()
            except Exception:
                log.exception("No se pudo construir el pipeline del trabajo %s", id_trabajo)
                raise StageError(SEGMENTACION, MENSAJE_MODELO)
            progreso = _crear_progreso()
            progreso.attach(DatabaseRecorder(self._sf, id_trabajo))
            inicio = time.perf_counter()
            salida = pipeline.run(entrada, progreso)
            self._completar(id_trabajo, salida, time.perf_counter() - inicio)
        except StageError as exc:
            self._fallar(id_trabajo, exc.stage, exc.message)
        except Exception:
            # El detalle va al log; al usuario solo se le muestra un mensaje general
            log.exception("Error inesperado en el trabajo %s", id_trabajo)
            self._fallar(id_trabajo, None, MENSAJE_ERROR_GENERICO)

    def _preparar_entrada(self, id_trabajo: int) -> Any:
        with self._sf() as s:
            trabajo = s.get(Trabajo, id_trabajo)
            estudio = s.get(Estudio, trabajo.id_estudio)
            imagen, referencia = [], []
            for archivo in sorted(estudio.archivos, key=lambda a: a.ruta):
                destino = referencia if "/referencia/" in archivo.ruta else imagen
                destino.append(self._storage.absoluta(archivo.ruta))
            return _crear_entrada(
                files=imagen, fmt=estudio.formato, reference_files=referencia,
                output_dir=self._storage.carpeta_resultado(id_trabajo),
            )

    def _completar(self, id_trabajo: int, salida: Any, segundos: float) -> None:
        ruta_mascara = self._storage.relativa(Path(salida.mask_path))
        with self._sf() as s:
            ResultRepository(s).crear(
                id_trabajo, ruta_mascara, salida.dice, salida.iou, segundos
            )
            trabajo = s.get(Trabajo, id_trabajo)
            job = Job(trabajo.estado)
            job.completar()
            trabajo.estado, trabajo.fecha_fin = job.estado, ahora()
            s.commit()

    def _fallar(self, id_trabajo: int, etapa: str | None, mensaje: str) -> None:
        with self._sf() as s:
            trabajo = s.get(Trabajo, id_trabajo)
            job = Job(trabajo.estado)
            job.fallar()
            etapas = JobRepository(s).etapas(id_trabajo)
            # Etapa que estaba corriendo (si el pipeline no alcanzó a notificar el fallo)
            for e in etapas:
                if e.estado == EN_PROCESO or (e.nombre == etapa and e.estado == PENDIENTE):
                    e.estado, e.fecha_fin = FALLIDO, ahora()
                    etapa = etapa or e.nombre
            trabajo.estado, trabajo.fecha_fin = job.estado, ahora()
            trabajo.etapa_fallida, trabajo.mensaje_error = etapa, mensaje
            s.commit()
