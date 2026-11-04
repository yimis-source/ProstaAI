"""Fixtures compartidas de las pruebas del pipeline."""
from __future__ import annotations

from pathlib import Path

import nibabel as nib
import numpy as np
import pytest

from datos_sinteticos import esfera
from prosta_ai.pipeline.preparation import PreparationConfig


@pytest.fixture
def affine_demo() -> np.ndarray:
    a = np.diag([1.5, 1.5, 3.0, 1.0])
    a[:3, 3] = [-30.0, -20.0, 5.0]
    return a


@pytest.fixture
def nifti_path(tmp_path: Path, affine_demo) -> Path:
    p = tmp_path / "estudio.nii.gz"
    nib.save(nib.Nifti1Image(esfera(), affine_demo), str(p))
    return p


@pytest.fixture
def referencia_path(tmp_path: Path, affine_demo) -> Path:
    ref = (esfera() > 300).astype(np.uint8)
    p = tmp_path / "ref.nii.gz"
    nib.save(nib.Nifti1Image(ref, affine_demo), str(p))
    return p


@pytest.fixture
def config_prep() -> PreparationConfig:
    return PreparationConfig(
        nombre="umbral", version="test", espaciado=(1.0, 1.0, 1.0), red={}, normalizar_intensidad=True
    )
