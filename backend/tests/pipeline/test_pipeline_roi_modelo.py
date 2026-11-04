import json

import nibabel as nib
import numpy as np
import pytest

from prosta_ai.pipeline.errors import StageError
from prosta_ai.pipeline.factory import build_pipeline, model_info
from prosta_ai.pipeline.io import load_volume
from prosta_ai.pipeline.preparation import prepare_volume
from prosta_ai.pipeline.roi import mask_to_original_space
from prosta_ai.pipeline.segmentation import NnUNetStrategy, PretrainedUNetStrategy, create_strategy
from datos_sinteticos import EstrategiaUmbral


@pytest.mark.parametrize("orientacion_afin", ["ras", "lps", "rotada"])
def test_mascara_vuelve_al_espacio_original(nifti_path, config_prep, tmp_path, orientacion_afin):
    img = nib.load(str(nifti_path))
    affine = img.affine.copy()
    if orientacion_afin == "lps":
        affine[:2] *= -1
    elif orientacion_afin == "rotada":
        affine[:, [0, 1]] = affine[:, [1, 0]]  # ejes x e y intercambiados
    p = tmp_path / "o.nii.gz"
    nib.save(nib.Nifti1Image(np.asarray(img.dataobj), affine), str(p))
    vol = load_volume([p], "NIfTI")
    prep = prepare_volume(vol, config_prep)
    mask = EstrategiaUmbral(1.0).segment(prep)
    orig = mask_to_original_space(mask, prep, vol)
    assert orig.shape == vol.data.shape and orig.dtype == np.uint8
    # el objeto se encuentra donde estaba la elipsoide brillante
    ref = (vol.data > 300)
    inter = (orig > 0) & ref
    assert 2 * inter.sum() / (orig.sum() + ref.sum()) > 0.8


def test_sin_pesos_mensaje_claro(tmp_path, nifti_path, config_prep):
    carpeta = tmp_path / "modelos" / "prostate_mri_anatomy"
    est = create_strategy("prostate_mri_anatomy", tmp_path / "modelos")
    assert isinstance(est, PretrainedUNetStrategy)
    vol = load_volume([nifti_path], "NIfTI")
    with pytest.raises(StageError) as e:
        est.segment(prepare_volume(vol, config_prep))
    assert e.value.stage == "segmentación"
    assert "descargar_modelo.py" in e.value.message and "No se encontraron los pesos" in e.value.message
    assert not carpeta.exists()


def test_config_sin_pesos_y_model_info(tmp_path, config_prep):
    carpeta = tmp_path / "m"
    carpeta.mkdir()
    (carpeta / "preparacion.json").write_text(json.dumps({
        "nombre": "prostate_mri_anatomy", "version": "9.9", "orientacion": "RAS",
        "espaciado": [0.5, 0.5, 0.5], "roi_size": [96, 96, 96], "red": {"spatial_dims": 3},
    }))
    info = model_info("prostate_mri_anatomy", carpeta)
    assert info["version"] == "9.9" and info["hash_pesos"] is None
    assert info["ruta_configuracion"].endswith("preparacion.json")
    assert set(info) == {"nombre", "version", "ruta_pesos", "hash_pesos", "ruta_configuracion"}
    (carpeta / "models").mkdir()
    (carpeta / "models" / "model.pt").write_bytes(b"abc")
    assert model_info("prostate_mri_anatomy", carpeta)["hash_pesos"] == (
        "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
    )
    assert build_pipeline("prostate_mri_anatomy", carpeta).strategy.version == "9.9"


def test_carga_perezosa_de_pesos_una_vez(tmp_path, nifti_path):
    """Con una red mínima: los pesos se cargan en la primera inferencia y se reutilizan."""
    import torch
    from monai.networks.nets import UNet

    red = {"spatial_dims": 3, "in_channels": 1, "out_channels": 3, "channels": [4, 8], "strides": [2],
           "num_res_units": 1, "norm": "batch", "act": "prelu", "dropout": 0.0}
    carpeta = tmp_path / "mini"
    (carpeta / "models").mkdir(parents=True)
    torch.save(UNet(**red).state_dict(), carpeta / "models" / "model.pt")
    (carpeta / "preparacion.json").write_text(json.dumps({
        "nombre": "mini", "version": "1", "orientacion": "RAS", "espaciado": [2, 2, 2],
        "roi_size": [16, 16, 16], "sw_batch_size": 2, "overlap": 0.25, "red": red,
        "etiquetas_prostata": [1, 2],
    }))
    est = PretrainedUNetStrategy(carpeta)
    assert est._model is None
    prep = prepare_volume(load_volume([nifti_path], "NIfTI"), est.config)
    m1 = est.segment(prep)
    modelo = est._model
    m2 = est.segment(prep)
    assert est._model is modelo and np.array_equal(m1, m2)
    assert m1.shape == tuple(prep.tensor.shape[1:]) and m1.dtype == np.uint8


def test_nnunet_reservado(tmp_path, nifti_path, config_prep):
    est = create_strategy("nnunet", tmp_path)
    assert isinstance(est, NnUNetStrategy)
    prep = prepare_volume(load_volume([nifti_path], "NIfTI"), config_prep)
    with pytest.raises(StageError, match="nnU-Net"):
        est.segment(prep)


def test_modelo_desconocido(tmp_path):
    with pytest.raises(StageError):
        create_strategy("otro", tmp_path)


def test_modelo_propio_con_nombre_libre(tmp_path):
    """Un modelo entrenado por el equipo se reconoce por su preparacion.json."""
    carpeta = tmp_path / "prostata_task05_ajustado"
    carpeta.mkdir()
    (carpeta / "preparacion.json").write_text(json.dumps({
        "nombre": "prostata_task05_ajustado", "version": "1", "orientacion": "RAS",
        "espaciado": [2, 2, 2], "roi_size": [16, 16, 16], "red": {}, "etiquetas_prostata": [1, 2],
    }))
    assert isinstance(create_strategy("prostata_task05_ajustado", tmp_path), PretrainedUNetStrategy)
    with pytest.raises(StageError):
        create_strategy("no_existe", tmp_path / "vacio")
