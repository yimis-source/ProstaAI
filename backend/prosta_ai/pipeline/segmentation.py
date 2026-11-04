"""Segmentación 3D (patrón Strategy + Factory Method)."""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

import numpy as np
import SimpleITK as sitk
import torch
from monai.inferers import SlidingWindowInferer
from monai.networks.nets import UNet

from .errors import StageError
from .preparation import PreparationConfig, PreparedVolume
from .stages import SEGMENTACION

NOMBRES_UNET = ("prostate_mri_anatomy", "pretrained_unet", "unet")
NOMBRES_NNUNET = ("nnunet", "nn_unet")


def resolve_model_dir(name: str, weights_dir: Path) -> Path:
    """Carpeta que contiene `preparacion.json`: `weights_dir` o `weights_dir/<name>`."""
    weights_dir = Path(weights_dir)
    if (weights_dir / "preparacion.json").exists():
        return weights_dir
    if (weights_dir / name / "preparacion.json").exists():
        return weights_dir / name
    return weights_dir


class SegmentationStrategy(ABC):
    """Algoritmo de segmentación intercambiable."""

    name: str = ""
    version: str = ""
    weights_path: Path | None = None

    @abstractmethod
    def segment(self, prepared: PreparedVolume) -> np.ndarray:
        """Devuelve una máscara binaria uint8 en el espacio preparado, forma (X, Y, Z)."""


def _mayor_componente(binaria: np.ndarray) -> np.ndarray:
    """Conserva solo la componente conexa más grande de una máscara binaria."""
    if not binaria.any():
        return binaria
    img = sitk.GetImageFromArray(binaria.astype(np.uint8))
    cc = sitk.RelabelComponent(sitk.ConnectedComponent(img), sortByObjectSize=True)
    return sitk.GetArrayFromImage(cc) == 1


class PretrainedUNetStrategy(SegmentationStrategy):
    """UNet de MONAI con pesos preentrenados (bundle prostate_mri_anatomy u otro compatible).

    La arquitectura, la ventana deslizante y el posproceso salen de `preparacion.json`.
    Los pesos se cargan una sola vez por instancia, en la primera inferencia.
    """

    def __init__(self, weights_dir: Path, device: str | None = None):
        self.weights_dir = Path(weights_dir)
        self.config_path = self.weights_dir / "preparacion.json"
        self._config: PreparationConfig | None = None
        self._model: torch.nn.Module | None = None
        self._device = torch.device(device or ("cuda" if torch.cuda.is_available() else "cpu"))
        self.name = self.weights_dir.name
        self.version = ""
        self.weights_path = None
        if self.config_path.exists():
            self._config = PreparationConfig.from_json(self.config_path)
            self.name = self._config.nombre
            self.version = self._config.version
            self.weights_path = self.weights_dir / self._config.pesos

    @property
    def config(self) -> PreparationConfig:
        if self._config is None:
            raise StageError(SEGMENTACION, self._mensaje_sin_pesos())
        return self._config

    def _mensaje_sin_pesos(self) -> str:
        return (
            f"No se encontraron los pesos del modelo en {self.weights_dir}; "
            "ejecute scripts/descargar_modelo.py"
        )

    def _cargar_modelo(self) -> torch.nn.Module:
        if self._model is not None:
            return self._model
        cfg = self.config
        if self.weights_path is None or not self.weights_path.exists():
            raise StageError(SEGMENTACION, self._mensaje_sin_pesos())
        try:
            red = UNet(**cfg.red)
            estado = torch.load(self.weights_path, map_location="cpu", weights_only=True)
            if isinstance(estado, dict) and "model" in estado:  # formato de checkpoint de ignite
                estado = estado["model"]
            red.load_state_dict(estado)
        except Exception as exc:
            raise StageError(SEGMENTACION, "Los pesos del modelo están dañados o no son compatibles.") from exc
        self._model = red.to(self._device).eval()
        return self._model

    def segment(self, prepared: PreparedVolume) -> np.ndarray:
        cfg = self.config
        modelo = self._cargar_modelo()
        inferer = SlidingWindowInferer(
            roi_size=cfg.roi_size, sw_batch_size=cfg.sw_batch_size, overlap=cfg.overlap
        )
        try:
            with torch.inference_mode():
                x = prepared.tensor[None].to(self._device)  # (1, 1, X, Y, Z)
                logits = inferer(x, modelo)
                etiquetas = logits.argmax(dim=1)[0].cpu().numpy().astype(np.uint8)
        except Exception as exc:
            raise StageError(SEGMENTACION, "Falló la inferencia del modelo.") from exc
        # zonas (TZ/PZ): la próstata completa es la unión de las etiquetas > 0,
        # conservando antes el mayor componente de cada etiqueta como en el bundle
        mascara = np.zeros(etiquetas.shape, dtype=bool)
        for etiqueta in cfg.etiquetas_prostata:
            zona = etiquetas == etiqueta
            mascara |= _mayor_componente(zona) if cfg.conservar_mayor_componente else zona
        return mascara.astype(np.uint8)


class NnUNetStrategy(SegmentationStrategy):
    """Reservada para nnU-Net; hoy solo informa que no está disponible."""

    name = "nnunet"
    version = "no disponible"

    def __init__(self, weights_dir: Path):
        self.weights_path = Path(weights_dir)

    def segment(self, prepared: PreparedVolume) -> np.ndarray:
        raise StageError(
            SEGMENTACION, "La estrategia nnU-Net aún no está disponible en esta versión; use el modelo UNet preentrenado."
        )


def create_strategy(name: str, weights_dir: Path) -> SegmentationStrategy:
    """Factory Method: crea la estrategia según el nombre configurado."""
    clave = name.strip().lower()
    if clave in NOMBRES_UNET:
        return PretrainedUNetStrategy(resolve_model_dir(name, weights_dir))
    if clave in NOMBRES_NNUNET:
        return NnUNetStrategy(weights_dir)
    # Un modelo propio (p. ej. entrenado en Colab) se reconoce por su preparacion.json
    carpeta = resolve_model_dir(name, weights_dir)
    if (carpeta / "preparacion.json").exists():
        return PretrainedUNetStrategy(carpeta)
    raise StageError(SEGMENTACION, f"Modelo desconocido: {name}.")
