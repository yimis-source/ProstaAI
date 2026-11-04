import json
from pathlib import Path

import nibabel as nib
import numpy as np
import torch

from entrenamiento.entrenar import config_a_json, preparar_etiqueta
from prosta_ai.pipeline.preparation import PreparationConfig


def _cfg() -> PreparationConfig:
    return PreparationConfig(
        nombre="demo", version="0.0.1", espaciado=(1.0, 1.0, 1.0), roi_size=(32, 32, 32),
        red={"spatial_dims": 3, "in_channels": 1, "out_channels": 3, "channels": [4, 8], "strides": [2]},
    )


def test_preparacion_json_se_puede_releer(tmp_path: Path):
    cfg = _cfg()
    ruta = tmp_path / "preparacion.json"
    ruta.write_text(json.dumps(config_a_json(cfg)))
    assert PreparationConfig.from_json(ruta) == cfg  # create_strategy lee el mismo archivo


def test_etiqueta_msd_se_intercambia_y_conserva_la_union(tmp_path: Path):
    et = np.zeros((8, 8, 8), dtype=np.uint8)
    et[1:4, 1:4, 1:4] = 1  # MSD: zona periférica
    et[4:7, 4:7, 4:7] = 2  # MSD: zona de transición
    ruta = tmp_path / "et.nii.gz"
    nib.save(nib.Nifti1Image(et, np.eye(4)), str(ruta))
    out = preparar_etiqueta(ruta, _cfg())
    assert out.shape == (1, 8, 8, 8)
    assert int(out[0, 2, 2, 2]) == 2 and int(out[0, 5, 5, 5]) == 1  # modelo base: 1 = central, 2 = periférica
    assert torch.equal(out > 0, torch.from_numpy(et[None] > 0))
