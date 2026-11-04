"""Contraseñas con bcrypt y token firmado (JWT HS256)."""
from datetime import timedelta

import bcrypt
import jwt

from prosta_ai.db import ahora

ALGORITMO = "HS256"
ROUNDS = 12  # las pruebas lo reducen para ir más rápido


class TokenInvalido(Exception):
    """El token no existe, está alterado o venció."""


def hash_password(password: str) -> str:
    # bcrypt solo usa los primeros 72 bytes
    datos = password.encode("utf-8")[:72]
    return bcrypt.hashpw(datos, bcrypt.gensalt(rounds=ROUNDS)).decode("ascii")


def verify_password(password: str, hash_guardado: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8")[:72], hash_guardado.encode("ascii"))
    except ValueError:
        return False


def create_token(id_usuario: int, alias: str, secret: str, horas: int) -> str:
    ahora_utc = ahora()
    payload = {
        "sub": str(id_usuario),
        "alias": alias,
        "iat": ahora_utc,
        "exp": ahora_utc + timedelta(hours=horas),
    }
    return jwt.encode(payload, secret, algorithm=ALGORITMO)


def decode_token(token: str, secret: str) -> dict:
    try:
        return jwt.decode(token, secret, algorithms=[ALGORITMO])
    except jwt.PyJWTError as exc:
        raise TokenInvalido(str(exc)) from exc
