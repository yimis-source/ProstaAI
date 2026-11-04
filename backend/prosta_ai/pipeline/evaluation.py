"""Métricas de comparación entre la máscara obtenida y la referencia."""
from __future__ import annotations

import numpy as np


def _binarias(pred: np.ndarray, ref: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    p = np.asarray(pred) > 0
    r = np.asarray(ref) > 0
    if p.shape != r.shape:
        raise ValueError(f"Las máscaras tienen formas distintas: {p.shape} y {r.shape}")
    return p, r


def dice(pred: np.ndarray, ref: np.ndarray) -> float:
    """Coeficiente de Dice entre dos máscaras binarias. Ambas vacías -> 1.0."""
    p, r = _binarias(pred, ref)
    total = int(p.sum()) + int(r.sum())
    if total == 0:
        return 1.0
    return float(2.0 * np.logical_and(p, r).sum() / total)


def iou(pred: np.ndarray, ref: np.ndarray) -> float:
    """Índice de Jaccard (IoU) entre dos máscaras binarias. Ambas vacías -> 1.0."""
    p, r = _binarias(pred, ref)
    union = int(np.logical_or(p, r).sum())
    if union == 0:
        return 1.0
    return float(np.logical_and(p, r).sum() / union)
