import numpy as np
import pytest

from prosta_ai.pipeline.evaluation import dice, iou


def test_identicas():
    m = np.zeros((4, 4, 4), np.uint8)
    m[1:3, 1:3, 1:3] = 1
    assert dice(m, m) == 1.0 and iou(m, m) == 1.0


def test_disjuntas():
    a = np.zeros((4, 4, 4), np.uint8)
    b = a.copy()
    a[0] = 1
    b[3] = 1
    assert dice(a, b) == 0.0 and iou(a, b) == 0.0


def test_solape_parcial():
    a = np.zeros(10, np.uint8)
    b = np.zeros(10, np.uint8)
    a[:4] = 1  # 4 vóxeles
    b[2:6] = 1  # 4 vóxeles, 2 en común
    assert dice(a, b) == pytest.approx(2 * 2 / 8)
    assert iou(a, b) == pytest.approx(2 / 6)


def test_ambos_vacios():
    z = np.zeros((3, 3, 3))
    assert dice(z, z) == 1.0 and iou(z, z) == 1.0


def test_uno_vacio():
    a = np.ones((3, 3, 3))
    assert dice(a, np.zeros_like(a)) == 0.0


def test_formas_distintas():
    with pytest.raises(ValueError):
        dice(np.zeros((2, 2)), np.zeros((3, 3)))
