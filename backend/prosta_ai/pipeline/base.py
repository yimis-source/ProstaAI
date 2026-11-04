"""Orden fijo del procesamiento (patrón Template Method)."""
from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from . import stages
from .errors import StageError
from .evaluation import dice, iou
from .io import Volume, deidentify_dicom, expand_dicom_files, load_volume, save_nifti
from .preparation import PreparationConfig, PreparedVolume, prepare_volume
from .progress import PipelineProgress, TimingRecorder
from .roi import mask_to_original_space
from .segmentation import SegmentationStrategy
from .validators import detailed_validation


@dataclass
class PipelineInput:
    files: list[Path]
    fmt: str
    reference_files: list[Path]
    output_dir: Path


@dataclass
class PipelineOutput:
    image_path: Path
    mask_path: Path
    dice: float | None
    iou: float | None
    durations: dict[str, float]


@dataclass
class PipelineContext:
    """Estado compartido entre etapas durante una ejecución."""

    volume: Volume | None = None
    reference: np.ndarray | None = None  # máscara de referencia binaria
    prepared: PreparedVolume | None = None
    mask: np.ndarray | None = None  # en el espacio preparado
    mask_original: np.ndarray | None = None
    image_path: Path | None = None
    mask_path: Path | None = None
    dice: float | None = None
    iou: float | None = None


class BasePipeline(ABC):
    """Define `run`; las subclases implementan cada etapa."""

    def run(self, inp: PipelineInput, progress: PipelineProgress) -> PipelineOutput:
        ctx = PipelineContext()
        timing = TimingRecorder()
        progress.attach(timing)
        etapas = [
            (stages.CONTROL_CALIDAD, self.quality_control),
            (stages.PREPARACION, self.prepare),
            (stages.SEGMENTACION, self.segment),
            (stages.ROI, self.build_roi),
            (stages.EVALUACION, self.evaluate),
        ]
        for nombre, funcion in etapas:
            progress.notify_start(nombre)
            t0 = time.perf_counter()
            try:
                funcion(inp, ctx)
            except StageError as exc:
                progress.notify_failed(nombre, exc.message)
                raise
            except Exception as exc:  # error no previsto: se informa de forma controlada
                err = StageError(nombre, "Ocurrió un error inesperado durante esta etapa.")
                progress.notify_failed(nombre, err.message)
                raise err from exc
            progress.notify_end(nombre, time.perf_counter() - t0)
        assert ctx.image_path is not None and ctx.mask_path is not None
        return PipelineOutput(
            image_path=ctx.image_path,
            mask_path=ctx.mask_path,
            dice=ctx.dice,
            iou=ctx.iou,
            durations=dict(timing.durations),
        )

    @abstractmethod
    def quality_control(self, inp: PipelineInput, ctx: PipelineContext) -> None: ...

    @abstractmethod
    def prepare(self, inp: PipelineInput, ctx: PipelineContext) -> None: ...

    @abstractmethod
    def segment(self, inp: PipelineInput, ctx: PipelineContext) -> None: ...

    @abstractmethod
    def build_roi(self, inp: PipelineInput, ctx: PipelineContext) -> None: ...

    @abstractmethod
    def evaluate(self, inp: PipelineInput, ctx: PipelineContext) -> None: ...


def _leer_referencia(files: list[Path], fmt: str) -> Volume:
    """La referencia es un NIfTI o, si no, una serie del mismo formato que el estudio."""
    if len(files) == 1 and files[0].name.lower().endswith((".nii", ".nii.gz")):
        return load_volume(files, "NIfTI")
    return load_volume(files, fmt)


class Segmentation3DPipeline(BasePipeline):
    """Segmentación 3D de la próstata con la estrategia indicada."""

    def __init__(self, strategy: SegmentationStrategy, config: PreparationConfig | None = None):
        self.strategy = strategy
        # por defecto la configuración sale de la propia estrategia (si la tiene)
        self._config = config

    def _preparation_config(self) -> PreparationConfig:
        cfg = self._config or getattr(self.strategy, "config", None)
        if cfg is None:
            raise StageError(stages.PREPARACION, "El modelo no tiene configuración de preparación.")
        return cfg

    def quality_control(self, inp: PipelineInput, ctx: PipelineContext) -> None:
        files = [Path(f) for f in inp.files]
        ref_files = [Path(f) for f in inp.reference_files]
        if inp.fmt == "DICOM":
            # antes de leer: nada identificativo llega al resto del proceso. Se pasan los
            # archivos tal como se guardaron para que también se borre el .zip original.
            deidentify_dicom(files)
            files = expand_dicom_files(files)
        dicom_ref = [f for f in ref_files if f.suffix.lower() in (".dcm", ".zip")]
        if dicom_ref:
            deidentify_dicom(dicom_ref)
        volume = load_volume(files, inp.fmt)
        reference = _leer_referencia(ref_files, inp.fmt) if ref_files else None
        detailed_validation(volume, reference)
        ctx.volume = volume
        if reference is not None:
            ctx.reference = (reference.data > 0).astype(np.uint8)

    def prepare(self, inp: PipelineInput, ctx: PipelineContext) -> None:
        assert ctx.volume is not None
        ctx.prepared = prepare_volume(ctx.volume, self._preparation_config())

    def segment(self, inp: PipelineInput, ctx: PipelineContext) -> None:
        assert ctx.prepared is not None
        ctx.mask = self.strategy.segment(ctx.prepared)

    def build_roi(self, inp: PipelineInput, ctx: PipelineContext) -> None:
        assert ctx.volume is not None and ctx.prepared is not None and ctx.mask is not None
        ctx.mask_original = mask_to_original_space(ctx.mask, ctx.prepared, ctx.volume)
        out = Path(inp.output_dir)
        ctx.image_path = out / "imagen.nii.gz"
        ctx.mask_path = out / "mascara.nii.gz"
        save_nifti(ctx.volume.data, ctx.volume.affine, ctx.image_path)
        save_nifti(ctx.mask_original, ctx.volume.affine, ctx.mask_path)

    def evaluate(self, inp: PipelineInput, ctx: PipelineContext) -> None:
        if ctx.reference is None or ctx.mask_original is None:
            return  # sin referencia: dice = iou = None
        ctx.dice = dice(ctx.mask_original, ctx.reference)
        ctx.iou = iou(ctx.mask_original, ctx.reference)
