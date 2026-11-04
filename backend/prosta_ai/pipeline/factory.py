"""Construcción del pipeline y datos del modelo para registrarlo."""
from __future__ import annotations

import hashlib
from pathlib import Path

from .base import Segmentation3DPipeline
from .segmentation import PretrainedUNetStrategy, create_strategy, resolve_model_dir


def build_pipeline(model_name: str, model_dir: Path) -> Segmentation3DPipeline:
    """Crea el pipeline con la estrategia indicada. Los pesos se cargan al primer uso."""
    return Segmentation3DPipeline(create_strategy(model_name, model_dir))


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def model_info(model_name: str, model_dir: Path) -> dict:
    """Datos para la tabla `modelo`: nombre, versión, rutas y hash de los pesos (o None)."""
    estrategia = create_strategy(model_name, model_dir)
    pesos = estrategia.weights_path
    hay_pesos = pesos is not None and Path(pesos).is_file()
    config = None
    if isinstance(estrategia, PretrainedUNetStrategy):
        config = estrategia.config_path if estrategia.config_path.exists() else None
    return {
        "nombre": estrategia.name or model_name,
        "version": estrategia.version or "desconocida",
        "ruta_pesos": str(pesos) if pesos is not None else None,
        "hash_pesos": _sha256(Path(pesos)) if hay_pesos else None,
        "ruta_configuracion": str(config) if config is not None else None,
    }
