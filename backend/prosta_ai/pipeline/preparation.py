"""Preparación del volumen para el modelo.

Las MISMAS transformaciones se usan en entrenamiento e inferencia (RF-09): se
describen en un JSON versionado junto a los pesos (`preparacion.json`), que
para el bundle `prostate_mri_anatomy` se genera a partir de su `inference.json`.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import torch
from monai.data import MetaTensor
from monai.transforms import (
    Compose,
    EnsureTyped,
    NormalizeIntensityd,
    Orientationd,
    ScaleIntensityd,
    Spacingd,
)

from .errors import StageError
from .io import Volume
from .stages import PREPARACION


@dataclass
class PreparationConfig:
    """Parámetros de preparación e inferencia del modelo."""

    nombre: str
    version: str
    orientacion: str = "RAS"
    espaciado: tuple[float, float, float] = (0.5, 0.5, 0.5)
    modo_remuestreo: str = "bilinear"
    escala_min: float = 0.0
    escala_max: float = 1.0
    normalizar_intensidad: bool = True
    roi_size: tuple[int, int, int] = (96, 96, 96)
    sw_batch_size: int = 4
    overlap: float = 0.5
    red: dict = field(default_factory=dict)
    pesos: str = "models/model.pt"
    etiquetas_prostata: tuple[int, ...] = (1, 2)
    conservar_mayor_componente: bool = True

    @classmethod
    def from_json(cls, path: Path) -> "PreparationConfig":
        try:
            d = json.loads(Path(path).read_text(encoding="utf-8"))
            esc = d.get("escala_intensidad", {"min": 0, "max": 1})
            return cls(
                nombre=d["nombre"],
                version=str(d["version"]),
                orientacion=d["orientacion"],
                espaciado=tuple(float(v) for v in d["espaciado"]),
                modo_remuestreo=d.get("modo_remuestreo", "bilinear"),
                escala_min=float(esc["min"]),
                escala_max=float(esc["max"]),
                normalizar_intensidad=bool(d.get("normalizar_intensidad", True)),
                roi_size=tuple(int(v) for v in d["roi_size"]),
                sw_batch_size=int(d.get("sw_batch_size", 4)),
                overlap=float(d.get("overlap", 0.5)),
                red=dict(d["red"]),
                pesos=d.get("pesos", "models/model.pt"),
                etiquetas_prostata=tuple(int(v) for v in d.get("etiquetas_prostata", [1, 2])),
                conservar_mayor_componente=bool(d.get("conservar_mayor_componente", True)),
            )
        except (OSError, KeyError, ValueError, TypeError) as exc:
            raise StageError(PREPARACION, f"La configuración de preparación del modelo no es válida ({path}).") from exc


@dataclass
class PreparedVolume:
    """Volumen listo para el modelo y los datos para invertir la preparación."""

    tensor: torch.Tensor  # (1, X, Y, Z), float32, ya orientado, remuestreado y normalizado
    affine: np.ndarray  # afín del espacio preparado (4x4, RAS)
    original_shape: tuple[int, int, int]
    original_affine: np.ndarray
    config: PreparationConfig


def build_transforms(config: PreparationConfig) -> Compose:
    """Transformaciones sobre un diccionario {"image": MetaTensor canal-primero}."""
    pasos = [
        Orientationd(keys="image", axcodes=config.orientacion),
        Spacingd(keys="image", pixdim=config.espaciado, mode=config.modo_remuestreo),
        ScaleIntensityd(keys="image", minv=config.escala_min, maxv=config.escala_max),
    ]
    if config.normalizar_intensidad:
        pasos.append(NormalizeIntensityd(keys="image"))
    pasos.append(EnsureTyped(keys="image"))
    return Compose(pasos)


def prepare_volume(volume: Volume, config: PreparationConfig) -> PreparedVolume:
    """Aplica las transformaciones del modelo a un Volume."""
    try:
        img = MetaTensor(
            torch.from_numpy(volume.data[None].astype(np.float32)),
            affine=torch.as_tensor(volume.affine, dtype=torch.float64),
        )
        out = build_transforms(config)({"image": img})["image"]
        return PreparedVolume(
            tensor=torch.as_tensor(out).float().contiguous(),
            affine=np.asarray(out.affine, dtype=np.float64),
            original_shape=tuple(int(s) for s in volume.data.shape),
            original_affine=np.asarray(volume.affine, dtype=np.float64),
            config=config,
        )
    except StageError:
        raise
    except Exception as exc:
        raise StageError(PREPARACION, "No se pudo preparar el volumen para el modelo.") from exc
