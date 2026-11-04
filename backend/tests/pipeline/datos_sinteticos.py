"""Datos sintéticos de las pruebas del pipeline (sin red ni pesos reales)."""
from __future__ import annotations

import datetime
from pathlib import Path

import nibabel as nib
import numpy as np
import pydicom
import pytest
import SimpleITK as sitk
from pydicom.dataset import FileDataset, FileMetaDataset
from pydicom.uid import ExplicitVRLittleEndian, generate_uid

from prosta_ai.pipeline.preparation import PreparationConfig
from prosta_ai.pipeline.segmentation import SegmentationStrategy


def esfera(shape=(48, 48, 16), centro=(24, 24, 8), radios=(10, 10, 5)) -> np.ndarray:
    """Volumen con una elipsoide brillante sobre fondo con algo de ruido."""
    rng = np.random.default_rng(0)
    x, y, z = np.indices(shape)
    d = sum(((c - o) / r) ** 2 for c, o, r in zip((x, y, z), centro, radios))
    img = rng.normal(100, 5, shape).astype(np.float32)
    img[d <= 1] += 400
    return img


DATOS_FALSOS = {
    "PatientName": "Perez^Juan",
    "PatientID": "12345678",
    "PatientBirthDate": "19700101",
    "PatientSex": "M",
    "PatientAddress": "Calle Falsa 123",
    "InstitutionName": "Hospital Ficticio",
    "ReferringPhysicianName": "Doctor^Falso",
    "AccessionNumber": "ACC999",
    "StudyDate": "20240102",
    "StudyTime": "101010",
}


def escribir_serie_dicom(carpeta: Path, n: int = 10, con_datos_falsos: bool = True) -> list[Path]:
    """Escribe una serie DICOM sintética (n cortes de 40x40) con pydicom."""
    carpeta.mkdir(parents=True, exist_ok=True)
    estudio, serie, frame = generate_uid(), generate_uid(), generate_uid()
    rutas = []
    base = esfera(shape=(40, 40, n), centro=(20, 20, n // 2), radios=(8, 8, 3))
    for k in range(n):
        meta = FileMetaDataset()
        meta.MediaStorageSOPClassUID = pydicom.uid.MRImageStorage
        meta.MediaStorageSOPInstanceUID = generate_uid()
        meta.TransferSyntaxUID = ExplicitVRLittleEndian
        ruta = carpeta / f"corte_{k:03d}.dcm"
        ds = FileDataset(str(ruta), {}, file_meta=meta, preamble=b"\0" * 128)
        ds.SOPClassUID = meta.MediaStorageSOPClassUID
        ds.SOPInstanceUID = meta.MediaStorageSOPInstanceUID
        ds.StudyInstanceUID, ds.SeriesInstanceUID, ds.FrameOfReferenceUID = estudio, serie, frame
        ds.Modality = "MR"
        ds.InstanceNumber = k + 1
        if con_datos_falsos:
            for kw, v in DATOS_FALSOS.items():
                setattr(ds, kw, v)
            ds.add_new(0x00110010, "LO", "FABRICANTE_PRIVADO")
            ds.add_new(0x00111001, "LO", "dato privado")
        ds.Rows, ds.Columns = 40, 40
        ds.PixelSpacing = [1.0, 1.0]
        ds.SliceThickness = 3.0
        ds.ImageOrientationPatient = [1, 0, 0, 0, 1, 0]
        ds.ImagePositionPatient = [0.0, 0.0, 3.0 * k]
        ds.SamplesPerPixel = 1
        ds.PhotometricInterpretation = "MONOCHROME2"
        ds.BitsAllocated, ds.BitsStored, ds.HighBit, ds.PixelRepresentation = 16, 16, 15, 0
        ds.PixelData = base[:, :, k].T.astype(np.uint16).tobytes()  # filas = y
        ds.save_as(str(ruta))
        rutas.append(ruta)
    return rutas


class EstrategiaUmbral(SegmentationStrategy):
    """Estrategia falsa: umbraliza el volumen preparado."""

    name = "umbral"
    version = "test"
    weights_path = None

    def __init__(self, umbral: float = 0.0):
        self.umbral = umbral
        self.llamadas = 0

    def segment(self, prepared):
        self.llamadas += 1
        return (prepared.tensor[0].numpy() > self.umbral).astype(np.uint8)


