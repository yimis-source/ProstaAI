import logging
from typing import Callable

from sqlalchemy import select
from sqlalchemy.orm import Session

from prosta_ai.config import Settings
from prosta_ai.models import Modelo

log = logging.getLogger(__name__)


def _model_info_real(settings: Settings) -> dict:
    # Importación perezosa: el pipeline se carga solo cuando hace falta
    from prosta_ai.pipeline.factory import model_info

    return model_info(settings.modelo_nombre, settings.modelo_dir)


class ModelRepository:
    def __init__(self, db: Session):
        self.db = db

    def registrar_activo(
        self, settings: Settings, info_fn: Callable[[Settings], dict] = _model_info_real
    ) -> Modelo:
        """Registra (o recupera) el modelo activo. Si no se puede leer, usa lo disponible."""
        try:
            info = info_fn(settings)
        except Exception:
            log.exception("No se pudo leer la información del modelo; el fallo se verá al segmentar")
            info = {"nombre": settings.modelo_nombre, "version": "no disponible"}
        nombre = str(info.get("nombre") or settings.modelo_nombre)[:50]
        version = str(info.get("version") or "no disponible")[:20]
        modelo = self.db.scalar(
            select(Modelo).where(Modelo.nombre == nombre, Modelo.version == version)
        )
        if modelo is None:
            def texto(clave):
                valor = info.get(clave)
                return None if valor is None else str(valor)

            modelo = Modelo(
                nombre=nombre, version=version, ruta_pesos=texto("ruta_pesos"),
                hash_pesos=texto("hash_pesos"), ruta_configuracion=texto("ruta_configuracion"),
            )
            self.db.add(modelo)
            self.db.commit()
        return modelo
