"""Lectura y escritura de volúmenes (patrón Adapter sobre SimpleITK y nibabel).

Convención interna: `Volume.data` se indexa como en nibabel (x, y, z) y
`Volume.affine` lleva coordenadas RAS+ (mm). Los volúmenes DICOM se convierten
a esa misma convención al leerlos.
"""
from __future__ import annotations

import os
import shutil
import zipfile
from dataclasses import dataclass
from pathlib import Path

import nibabel as nib
import numpy as np
import pydicom
import SimpleITK as sitk

from .errors import StageError
from .stages import CONTROL_CALIDAD

MAX_ZIP_FILES = 20000
MAX_ZIP_BYTES = 4 * 1024**3  # tope de descompresión (contra zip bombs)


@dataclass
class Volume:
    """Volumen 3D en float32 con su geometría."""

    data: np.ndarray
    affine: np.ndarray
    spacing: tuple[float, float, float]


# ------------------------------------------------------------------ zip

def extract_zip_safely(zip_path: Path) -> list[Path]:
    """Extrae un .zip junto al propio archivo, sin permitir salir de la carpeta destino.

    Devuelve los archivos extraídos. Si ya se extrajo antes, reutiliza la carpeta.
    """
    destino = zip_path.parent / f"{zip_path.stem}_extraido"
    if destino.is_dir() and any(destino.rglob("*")):
        return sorted(p for p in destino.rglob("*") if p.is_file())
    destino.mkdir(parents=True, exist_ok=True)
    raiz = destino.resolve()
    try:
        with zipfile.ZipFile(zip_path) as zf:
            miembros = [m for m in zf.infolist() if not m.is_dir()]
            if len(miembros) > MAX_ZIP_FILES or sum(m.file_size for m in miembros) > MAX_ZIP_BYTES:
                raise StageError(CONTROL_CALIDAD, "El archivo .zip es demasiado grande al descomprimirse.")
            for m in miembros:
                partes = Path(m.filename.replace("\\", "/")).parts
                if "__MACOSX" in partes or partes[-1].startswith("."):
                    continue
                objetivo = (destino / Path(*partes)).resolve()
                if raiz != objetivo and raiz not in objetivo.parents:
                    raise StageError(CONTROL_CALIDAD, "El archivo .zip contiene rutas no permitidas.")
                objetivo.parent.mkdir(parents=True, exist_ok=True)
                with zf.open(m) as src, open(objetivo, "wb") as dst:
                    shutil.copyfileobj(src, dst)
    except zipfile.BadZipFile as exc:
        shutil.rmtree(destino, ignore_errors=True)
        raise StageError(CONTROL_CALIDAD, "El archivo .zip está dañado o no es válido.") from exc
    except StageError:
        shutil.rmtree(destino, ignore_errors=True)
        raise
    return sorted(p for p in destino.rglob("*") if p.is_file())


def _es_dicom(path: Path) -> bool:
    try:
        with open(path, "rb") as f:
            f.seek(128)
            return f.read(4) == b"DICM"
    except OSError:
        return False


def expand_dicom_files(files: list[Path]) -> list[Path]:
    """Sustituye cada .zip por los DICOM que contiene; deja el resto igual."""
    salida: list[Path] = []
    for f in files:
        f = Path(f)
        if f.suffix.lower() == ".zip":
            extraidos = [p for p in extract_zip_safely(f) if _es_dicom(p)]
            if not extraidos:
                raise StageError(CONTROL_CALIDAD, "El archivo .zip no contiene archivos DICOM.")
            salida.extend(extraidos)
        else:
            salida.append(f)
    return salida


# ---------------------------------------------------------------- lectura

def _sitk_a_volume(img: "sitk.Image") -> Volume:
    """Convierte una imagen de SimpleITK (LPS) a Volume (índices x,y,z y afín RAS)."""
    arr = sitk.GetArrayFromImage(img).astype(np.float32)  # (z, y, x)
    data = np.ascontiguousarray(arr.transpose(2, 1, 0))
    d = np.array(img.GetDirection()).reshape(3, 3)
    s = np.array(img.GetSpacing())
    lps = np.eye(4)
    lps[:3, :3] = d * s  # cada columna = dirección del índice * espaciado
    lps[:3, 3] = img.GetOrigin()
    affine = np.diag([-1.0, -1.0, 1.0, 1.0]) @ lps
    return Volume(data=data, affine=affine, spacing=(float(s[0]), float(s[1]), float(s[2])))


def _leer_serie_dicom(files: list[Path]) -> Volume:
    series: dict[str, list[tuple[float, Path]]] = {}
    for f in files:
        try:
            ds = pydicom.dcmread(str(f), stop_before_pixels=True)
        except Exception as exc:
            raise StageError(CONTROL_CALIDAD, f"El archivo DICOM {f.name} está dañado o no es legible.") from exc
        if "Rows" not in ds or "Columns" not in ds:
            raise StageError(CONTROL_CALIDAD, f"El archivo DICOM {f.name} está dañado o no contiene una imagen.")
        uid = str(getattr(ds, "SeriesInstanceUID", "sin_serie"))
        pos = getattr(ds, "ImagePositionPatient", None)
        ori = getattr(ds, "ImageOrientationPatient", None)
        if pos is not None and ori is not None:
            r = np.array(ori[:3], dtype=float)
            c = np.array(ori[3:], dtype=float)
            orden = float(np.dot(np.cross(r, c), np.array(pos, dtype=float)))
        else:
            orden = float(getattr(ds, "InstanceNumber", 0) or 0)
        series.setdefault(uid, []).append((orden, f))
    # si hay varias series se usa la que tiene más cortes
    elegida = max(series.values(), key=len)
    nombres = [str(p) for _, p in sorted(elegida, key=lambda t: t[0])]
    try:
        reader = sitk.ImageSeriesReader()
        reader.SetFileNames(nombres)
        img = reader.Execute()
    except Exception as exc:
        raise StageError(CONTROL_CALIDAD, "No se pudo reconstruir el volumen a partir de los cortes DICOM.") from exc
    if img.GetDimension() != 3:
        raise StageError(CONTROL_CALIDAD, "La serie DICOM no forma un volumen 3D.")
    return _sitk_a_volume(img)


def _leer_nifti(path: Path) -> Volume:
    """Lee un NIfTI. Si es 4D (p. ej. MSD Task05: canal 0 = T2, canal 1 = ADC) usa el canal 0."""
    try:
        img = nib.load(str(path))
        shape = img.shape
        if len(shape) == 4:
            data = np.asarray(img.dataobj[..., 0], dtype=np.float32)
        elif len(shape) == 3:
            data = np.asarray(img.dataobj, dtype=np.float32)
        else:
            raise StageError(CONTROL_CALIDAD, f"El volumen tiene {len(shape)} dimensiones; se esperaba 3D.")
        affine = np.array(img.affine, dtype=np.float64)
    except StageError:
        raise
    except Exception as exc:
        raise StageError(CONTROL_CALIDAD, f"El archivo {path.name} está dañado o no se puede leer.") from exc
    zooms = np.linalg.norm(affine[:3, :3], axis=0)
    return Volume(data=data, affine=affine, spacing=(float(zooms[0]), float(zooms[1]), float(zooms[2])))


def load_volume(files: list[Path], fmt: str) -> Volume:
    """Lee el estudio como un Volume. Lanza StageError("control de calidad", ...) si falla."""
    if not files:
        raise StageError(CONTROL_CALIDAD, "No hay archivos para leer.")
    if fmt == "NIfTI":
        if len(files) != 1:
            raise StageError(CONTROL_CALIDAD, "Un estudio NIfTI debe ser un único archivo.")
        return _leer_nifti(Path(files[0]))
    if fmt == "DICOM":
        return _leer_serie_dicom(expand_dicom_files([Path(f) for f in files]))
    raise StageError(CONTROL_CALIDAD, f"Formato desconocido: {fmt}")


# -------------------------------------------------------- desidentificación

# Perfil básico (PS3.15, tabla E.1-1) reducido a lo que puede identificar personas.
_TAGS_A_BORRAR = [
    "PatientName", "PatientID", "PatientBirthDate", "PatientBirthTime", "PatientSex",
    "PatientAge", "PatientSize", "PatientWeight", "PatientAddress", "PatientTelephoneNumbers",
    "PatientMotherBirthName", "PatientComments", "PatientInsurancePlanCodeSequence",
    "OtherPatientIDs", "OtherPatientNames", "OtherPatientIDsSequence", "EthnicGroup",
    "Occupation", "AdditionalPatientHistory", "MedicalRecordLocator", "MilitaryRank",
    "BranchOfService", "ResponsiblePerson", "ResponsibleOrganization",
    "InstitutionName", "InstitutionAddress", "InstitutionalDepartmentName",
    "ReferringPhysicianName", "ReferringPhysicianAddress", "ReferringPhysicianTelephoneNumbers",
    "PerformingPhysicianName", "PhysiciansOfRecord", "NameOfPhysiciansReadingStudy",
    "RequestingPhysician", "OperatorsName", "StationName", "DeviceSerialNumber",
    "AccessionNumber", "StudyID", "StudyDescription", "SeriesDescription", "ImageComments",
    "AdmittingDiagnosesDescription", "RequestAttributesSequence", "ReferencedPatientSequence",
    "ReferencedStudySequence", "ReferencedPerformedProcedureStepSequence",
    "PerformedProcedureStepID", "PerformedProcedureStepDescription",
    "StudyDate", "StudyTime", "SeriesDate", "SeriesTime", "AcquisitionDate", "AcquisitionTime",
    "AcquisitionDateTime", "ContentDate", "ContentTime", "InstanceCreationDate",
    "InstanceCreationTime", "PerformedProcedureStepStartDate", "PerformedProcedureStepStartTime",
]


def _borrar_tags(ds: pydicom.Dataset) -> None:
    """Elimina los tags identificativos, también dentro de secuencias."""
    for kw in _TAGS_A_BORRAR:
        if kw in ds:
            del ds[kw]
    ds.remove_private_tags()
    for elem in ds:
        if elem.VR == "SQ":
            for item in elem.value:
                _borrar_tags(item)


def deidentify_dicom(files: list[Path]) -> None:
    """Borra en sitio los tags que identifican personas. Lanza StageError si no puede.

    Si llegó un .zip, se desidentifican los archivos extraídos y después se borra el
    .zip original, que todavía conserva los datos de persona (RB-02). Si algún archivo
    no se puede desidentificar, se descartan todos los archivos del estudio (RF-05).
    """
    originales = [Path(f) for f in files]
    extraidos = expand_dicom_files(originales)
    for f in extraidos:
        try:
            ds = pydicom.dcmread(str(f))
            _borrar_tags(ds)
            ds.PatientIdentityRemoved = "YES"
            tmp = f.with_name(f.name + ".tmp")
            ds.save_as(str(tmp))
            os.replace(tmp, f)
        except Exception as exc:
            _descartar_archivos(originales + extraidos)
            raise StageError(
                CONTROL_CALIDAD,
                "No se pudo eliminar la información personal del estudio; el archivo fue rechazado y eliminado.",
            ) from exc
    for f in originales:
        if f.suffix.lower() == ".zip" and f.exists():
            f.unlink()


def _descartar_archivos(files: list[Path]) -> None:
    """Elimina archivos y las carpetas de extracción de los .zip."""
    for f in files:
        f.unlink(missing_ok=True)
        if f.suffix.lower() == ".zip":
            shutil.rmtree(f.parent / f"{f.stem}_extraido", ignore_errors=True)


# --------------------------------------------------------------- escritura

def save_nifti(data: np.ndarray, affine: np.ndarray, path: Path) -> None:
    """Guarda un NIfTI sin descripción ni metadatos de persona."""
    arr = np.asarray(data)
    if arr.dtype == np.float64:
        arr = arr.astype(np.float32)
    img = nib.Nifti1Image(arr, np.asarray(affine))
    img.header["descrip"] = b""
    img.header["db_name"] = b""
    img.header["aux_file"] = b""
    img.header.set_qform(img.affine, code=1)
    img.header.set_sform(img.affine, code=1)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    nib.save(img, str(path))
