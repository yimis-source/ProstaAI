"""Dependencias compartidas por los routers."""
from typing import Iterator

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from prosta_ai.models import Usuario
from prosta_ai.repositories import ModelRepository, UserRepository
from prosta_ai.security import TokenInvalido, decode_token

_bearer = HTTPBearer(auto_error=False)


def get_db(request: Request) -> Iterator[Session]:
    with request.app.state.session_factory() as session:
        yield session


def get_settings(request: Request):
    return request.app.state.settings


def get_storage(request: Request):
    return request.app.state.storage


def usuario_actual(
    request: Request,
    credenciales: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> Usuario:
    error = HTTPException(status_code=401, detail="Sesión no válida o vencida. Ingrese de nuevo.")
    if credenciales is None:
        raise error
    try:
        datos = decode_token(credenciales.credentials, request.app.state.settings.secret_key)
        usuario = UserRepository(db).por_id(int(datos["sub"]))
    except (TokenInvalido, KeyError, ValueError):
        raise error
    if usuario is None:
        raise error
    return usuario


def id_modelo_activo(request: Request, db: Session = Depends(get_db)) -> int:
    """Id del modelo activo; se registra la primera vez que hace falta."""
    app = request.app
    if getattr(app.state, "id_modelo", None) is None:
        modelo = ModelRepository(db).registrar_activo(app.state.settings, app.state.model_info_fn)
        app.state.id_modelo = modelo.id_modelo
    return app.state.id_modelo
