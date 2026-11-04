"""Cuerpos de entrada de la API."""
from pydantic import BaseModel, Field

ALIAS_PATRON = r"^[A-Za-z0-9_.-]{3,30}$"


class AliasEntrada(BaseModel):
    alias: str = Field(pattern=ALIAS_PATRON)


class AccesoEntrada(BaseModel):
    alias: str = Field(pattern=ALIAS_PATRON)
    contrasena: str = Field(min_length=1, max_length=128)
    confirmacion: str | None = Field(default=None, max_length=128)


class PreguntaEntrada(BaseModel):
    pregunta: str = Field(min_length=1, max_length=500)
