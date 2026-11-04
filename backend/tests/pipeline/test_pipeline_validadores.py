import gzip
import pytest

from prosta_ai.pipeline.errors import AdmissionError
from prosta_ai.pipeline.validators import UploadedFileInfo, validate_upload

NII = (348).to_bytes(4, "little") + b"\0" * 508
GZ = gzip.compress(b"x" * 600)[:512]
DCM = b"\0" * 128 + b"DICM" + b"\0" * 380
ZIP = b"PK\x03\x04" + b"\0" * 100
MB = 1024 * 1024


def f(nombre, head, size=1000):
    return UploadedFileInfo(nombre, size, head)


def test_nifti_gz_valido():
    assert validate_upload([f("a.nii.gz", GZ)], 10 * MB) == "NIfTI"


def test_nifti_sin_comprimir_valido():
    assert validate_upload([f("a.nii", NII)], 10 * MB) == "NIfTI"


def test_dicom_varios_y_zip():
    assert validate_upload([f("1.dcm", DCM), f("2.DCM", DCM)], 10 * MB) == "DICOM"
    assert validate_upload([f("serie.zip", ZIP)], 10 * MB) == "DICOM"


@pytest.mark.parametrize(
    "archivos",
    [
        [],
        [f("a.txt", b"hola")],
        [f("a.nii.gz", GZ), f("b.nii.gz", GZ)],
        [f("a.nii.gz", GZ), f("1.dcm", DCM)],
        [f("1.dcm", DCM), f("s.zip", ZIP)],
        [f("a.nii.gz", b"no es gzip")],
        [f("a.nii", b"\1\2\3\4" + b"\0" * 100)],
        [f("1.dcm", b"\0" * 200)],
        [f("s.zip", b"nozip")],
    ],
)
def test_rechazos_de_formato(archivos):
    with pytest.raises(AdmissionError) as e:
        validate_upload(archivos, 10 * MB)
    assert e.value.message


def test_tamano_excedido():
    with pytest.raises(AdmissionError, match="supera"):
        validate_upload([f("a.nii.gz", GZ, size=6 * MB), f("b.nii.gz", GZ, 1)][:1], 5 * MB)


def test_tamano_suma_varios_archivos():
    with pytest.raises(AdmissionError):
        validate_upload([f("1.dcm", DCM, 3 * MB), f("2.dcm", DCM, 3 * MB)], 5 * MB)
