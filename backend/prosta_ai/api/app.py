"""Fábrica de la aplicación FastAPI.

Arranque: uvicorn prosta_ai.api.app:create_app --factory
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from prosta_ai.api import acceso, asistente, estudios, trabajos
from prosta_ai.api.admision import admitir_con_pipeline
from prosta_ai.config import Settings, get_settings
from prosta_ai.db import create_db_engine, create_session_factory
from prosta_ai.processing.service import ProcessingService, pipeline_por_defecto
from prosta_ai.processing.worker import ProcessingWorker
from prosta_ai.repositories import ModelRepository
from prosta_ai.repositories.models import _model_info_real
from prosta_ai.storage import PrivateStorage

log = logging.getLogger(__name__)


def create_app(
    settings: Settings | None = None, *, pipeline_provider=None, admission=None,
    model_info_fn=None,
) -> FastAPI:
    """Los parámetros opcionales permiten inyectar un pipeline, una admisión o un
    lector de modelo distintos (pruebas)."""
    settings = settings or get_settings()
    engine = create_db_engine(settings.database_url)
    session_factory = create_session_factory(engine)
    storage = PrivateStorage(settings.storage_dir)
    service = ProcessingService(
        session_factory, storage, pipeline_provider or pipeline_por_defecto(settings)
    )
    worker = ProcessingWorker(service, settings.worker_intervalo_s)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        try:
            with session_factory() as s:
                app.state.id_modelo = ModelRepository(s).registrar_activo(
                    settings, app.state.model_info_fn
                ).id_modelo
            service.recuperar_interrumpidos()
        except Exception:
            log.exception("No se pudo preparar el modelo al arrancar")
        if settings.worker_activo:
            worker.start()
        yield
        worker.stop()

    app = FastAPI(title="Prosta-AI", lifespan=lifespan)
    app.state.settings = settings
    app.state.engine = engine
    app.state.session_factory = session_factory
    app.state.storage = storage
    app.state.service = service
    app.state.worker = worker
    app.state.admission = admission or admitir_con_pipeline
    app.state.model_info_fn = model_info_fn or _model_info_real
    app.state.id_modelo = None

    app.add_middleware(
        CORSMiddleware, allow_origins=settings.cors_lista, allow_credentials=True,
        allow_methods=["*"], allow_headers=["*"],
    )

    @app.exception_handler(RequestValidationError)
    async def _validacion(_: Request, exc: RequestValidationError):
        campo = ".".join(str(p) for p in exc.errors()[0]["loc"][1:]) if exc.errors() else ""
        return JSONResponse(
            status_code=422, content={"detail": f"Datos no válidos en «{campo}»." if campo else "Datos no válidos."}
        )

    @app.get("/api/salud")
    def salud():
        return {"estado": "ok"}

    for router in (acceso.router, estudios.router, trabajos.router, asistente.router):
        app.include_router(router, prefix="/api")
    return app
