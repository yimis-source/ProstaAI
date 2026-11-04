"""Devuelve la máscara al espacio del volumen original (RF-12)."""
from __future__ import annotations

import numpy as np

from .errors import StageError
from .io import Volume
from .preparation import PreparedVolume
from .stages import ROI


def mask_to_original_space(mask: np.ndarray, prepared: PreparedVolume, original: Volume) -> np.ndarray:
    """Remuestrea (vecino más cercano) la máscara preparada a la rejilla de la imagen original.

    Para cada vóxel original se calcula su posición en mundo con la afín original
    y se busca el vóxel correspondiente en el espacio preparado. El resultado tiene
    la misma forma y la misma afín que la imagen original.
    """
    if mask.shape != tuple(prepared.tensor.shape[1:]):
        raise StageError(ROI, "La máscara no coincide con el volumen preparado.")
    shape = original.data.shape
    # coordenadas originales -> mundo -> índices preparados
    a = np.linalg.inv(prepared.affine) @ original.affine
    out = np.zeros(shape, dtype=np.uint8)
    ms = np.array(mask.shape)
    ii, jj = np.meshgrid(np.arange(shape[0]), np.arange(shape[1]), indexing="ij")
    for k in range(shape[2]):  # corte a corte para limitar la memoria
        idx = (
            a[:3, 0, None, None] * ii + a[:3, 1, None, None] * jj + a[:3, 2, None, None] * k + a[:3, 3, None, None]
        )
        idx = np.rint(idx).astype(np.int64)
        dentro = np.all((idx >= 0) & (idx < ms[:, None, None]), axis=0)
        corte = np.zeros(shape[:2], dtype=np.uint8)
        corte[dentro] = mask[idx[0][dentro], idx[1][dentro], idx[2][dentro]]
        out[:, :, k] = corte
    return (out > 0).astype(np.uint8)
