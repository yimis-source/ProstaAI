import time

import pytest

from prosta_ai import security
from prosta_ai.security import TokenInvalido


def test_hash_y_verificacion():
    h = security.hash_password("clave-segura-1")
    assert h != "clave-segura-1" and h.startswith("$2")
    assert security.verify_password("clave-segura-1", h)
    assert not security.verify_password("otra", h)
    assert not security.verify_password("x", "no-es-un-hash")


def test_token_valido():
    token = security.create_token(7, "ana", "secreto", 8)
    datos = security.decode_token(token, "secreto")
    assert datos["sub"] == "7" and datos["alias"] == "ana"


def test_token_clave_distinta_o_alterado():
    token = security.create_token(7, "ana", "secreto", 8)
    with pytest.raises(TokenInvalido):
        security.decode_token(token, "otra-clave")
    with pytest.raises(TokenInvalido):
        security.decode_token(token[:-3] + "abc", "secreto")


def test_token_vencido():
    token = security.create_token(7, "ana", "secreto", -1)
    with pytest.raises(TokenInvalido):
        security.decode_token(token, "secreto")
