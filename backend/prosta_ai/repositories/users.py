from sqlalchemy import select
from sqlalchemy.orm import Session

from prosta_ai.models import Usuario


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def por_alias(self, alias: str) -> Usuario | None:
        return self.db.scalar(select(Usuario).where(Usuario.alias == alias))

    def por_id(self, id_usuario: int) -> Usuario | None:
        return self.db.get(Usuario, id_usuario)

    def crear(self, alias: str, hash_contrasena: str) -> Usuario:
        usuario = Usuario(alias=alias, hash_contrasena=hash_contrasena)
        self.db.add(usuario)
        self.db.commit()
        return usuario
