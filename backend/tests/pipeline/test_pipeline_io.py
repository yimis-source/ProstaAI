import zipfile

import nibabel as nib
import numpy as np
import pydicom
import pytest

from prosta_ai.pipeline.errors import StageError
from prosta_ai.pipeline.io import (
    deidentify_dicom, extract_zip_safely, load_volume, save_nifti,
)
from datos_sinteticos import DATOS_FALSOS, escribir_serie_dicom

IDENTIFICATIVOS = list(DATOS_FALSOS)


def test_cargar_nifti_3d(nifti_path, affine_demo):
    v = load_volume([nifti_path], "NIfTI")
    assert v.data.shape == (48, 48, 16) and v.data.dtype == np.float32
    assert np.allclose(v.affine, affine_demo)
    assert v.spacing == pytest.approx((1.5, 1.5, 3.0))


def test_nifti_4d_usa_canal_0(tmp_path, affine_demo):
    t2 = np.full((40, 40, 10), 7, np.float32)
    t2[5:10] = 9
    adc = np.full((40, 40, 10), 100, np.float32)
    p = tmp_path / "msd.nii.gz"
    nib.save(nib.Nifti1Image(np.stack([t2, adc], -1), affine_demo), str(p))
    v = load_volume([p], "NIfTI")
    assert v.data.shape == (40, 40, 10)
    assert np.array_equal(v.data, t2)


def test_nifti_corrupto(tmp_path):
    p = tmp_path / "malo.nii.gz"
    p.write_bytes(b"\x1f\x8b" + b"basura" * 20)
    with pytest.raises(StageError) as e:
        load_volume([p], "NIfTI")
    assert e.value.stage == "control de calidad"


def test_dicom_serie(tmp_path):
    rutas = escribir_serie_dicom(tmp_path / "dcm", n=10)
    v = load_volume(rutas, "DICOM")
    assert v.data.shape == (40, 40, 10)
    assert v.spacing == pytest.approx((1.0, 1.0, 3.0))
    assert v.data.max() > 300  # el objeto brillante se conserva


def test_dicom_corrupto(tmp_path):
    rutas = escribir_serie_dicom(tmp_path / "dcm", n=10)
    rutas[3].write_bytes(b"\0" * 128 + b"DICM" + b"basura")
    with pytest.raises(StageError) as e:
        load_volume(rutas, "DICOM")
    assert e.value.stage == "control de calidad"


def test_desidentificar_borra_datos_personales(tmp_path):
    rutas = escribir_serie_dicom(tmp_path / "dcm", n=10)
    assert pydicom.dcmread(str(rutas[0])).PatientName == "Perez^Juan"
    deidentify_dicom(rutas)
    for r in rutas:
        ds = pydicom.dcmread(str(r))
        for kw in IDENTIFICATIVOS:
            assert kw not in ds, kw
        assert not any(e.tag.is_private for e in ds)
        assert ds.PatientIdentityRemoved == "YES"
    # sigue siendo una serie legible
    assert load_volume(rutas, "DICOM").data.shape == (40, 40, 10)


def test_zip_dicom_se_extrae_y_desidentifica(tmp_path):
    rutas = escribir_serie_dicom(tmp_path / "origen", n=10)
    z = tmp_path / "subida" / "serie.zip"
    z.parent.mkdir()
    with zipfile.ZipFile(z, "w") as zf:
        for r in rutas:
            zf.write(r, f"carpeta/{r.name}")
    deidentify_dicom([z])
    v = load_volume([z], "DICOM")
    assert v.data.shape == (40, 40, 10)
    extraidos = list((z.parent / "serie_extraido").rglob("*.dcm"))
    assert len(extraidos) == 10
    assert "PatientName" not in pydicom.dcmread(str(extraidos[0]))
    # el .zip original conserva datos de persona: no debe quedar guardado
    assert not z.exists()
    # un segundo procesamiento reutiliza la carpeta extraída
    assert load_volume([z], "DICOM").data.shape == (40, 40, 10)


def test_zip_path_traversal(tmp_path):
    z = tmp_path / "malo.zip"
    with zipfile.ZipFile(z, "w") as zf:
        zf.writestr("../../fuera.txt", "x")
    with pytest.raises(StageError):
        extract_zip_safely(z)
    assert not (tmp_path.parent / "fuera.txt").exists()
    assert not (tmp_path / "malo_extraido").exists()


def test_zip_invalido(tmp_path):
    z = tmp_path / "x.zip"
    z.write_bytes(b"no es zip")
    with pytest.raises(StageError):
        extract_zip_safely(z)


def test_save_nifti_sin_metadatos(tmp_path, affine_demo):
    p = tmp_path / "o" / "x.nii.gz"
    save_nifti(np.ones((4, 4, 4), np.float64), affine_demo, p)
    img = nib.load(str(p))
    assert bytes(img.header["descrip"]).strip(b"\0") == b""
    assert np.allclose(img.affine, affine_demo)
    assert img.get_data_dtype() == np.float32
