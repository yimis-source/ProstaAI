"""CU01: verificación de alias y acceso (DEC-01)."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from prosta_ai.api.deps import get_db, get_settings
from prosta_ai.api.schemas import AccesoEntrada, AliasEntrada
from prosta_ai.repositories import UserRepository
from prosta_ai.security import create_token, hash_password, verify_password

router = APIRouter(prefix="/acceso", tags=["acceso"])

MIN_CONTRASENA = 8


@router.post("/verificar")
def verificar(datos: AliasEntrada, db: Session = Depends(get_db)):
    return {"existe": UserRepository(db).por_alias(datos.alias) is not None}


@router.post("")
def acceder(datos: AccesoEntrada, db: Session = Depends(get_db), settings=Depends(get_settings)):
    repo = UserRepository(db)
    usuario = repo.por_alias(datos.alias)
    primer_acceso = usuario is None
    if primer_acceso:
        if len(datos.contrasena) < MIN_CONTRASENA:
            raise HTTPException(422, f"La contraseña debe tener al menos {MIN_CONTRASENA} caracteres.")
        if datos.confirmacion != datos.contrasena:
            raise HTTPException(422, "La confirmación no coincide con la contraseña.")
        try:
            usuario = repo.crear(datos.alias, hash_password(datos.contrasena))
        except IntegrityError:
            db.rollback()
            raise HTTPException(409, "El alias ya fue registrado. Intente ingresar de nuevo.")
    elif not verify_password(datos.contrasena, usuario.hash_contrasena):
        raise HTTPException(401, "Alias o contraseña incorrectos.")
    token = create_token(usuario.id_usuario, usuario.alias, settings.secret_key, settings.token_horas)
    return {"token": token, "alias": usuario.alias, "primer_acceso": primer_acceso}
