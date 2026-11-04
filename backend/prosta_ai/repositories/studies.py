from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from prosta_ai.constantes import LISTO_PARA_PROCESAR, NO_COMPATIBLE
from prosta_ai.models import Archivo, Estudio, Trabajo, Usuario


def estado_visible(estudio: Estudio) -> str:
    """Estado derivado para Mis estudios (no se guarda)."""
    if estudio.estado_admision == NO_COMPATIBLE:
        return NO_COMPATIBLE
    if not estudio.trabajos:
        return LISTO_PARA_PROCESAR
    return estudio.trabajos[-1].estado


class StudyRepository:
    def __init__(self, db: Session):
        self.db = db

    def siguiente_codigo(self) -> str:
        ultimo = self.db.scalar(select(func.max(Estudio.id_estudio))) or 0
        return f"EST-{ultimo + 1:04d}"

    def crear(self, usuario: Usuario, formato: str, estado_admision: str) -> Estudio:
        """Crea el estudio con código secuencial; reintenta si hay choque de código."""
        from sqlalchemy.exc import IntegrityError

        for _ in range(5):
            estudio = Estudio(
                codigo_anonimo=self.siguiente_codigo(), id_usuario=usuario.id_usuario,
                formato=formato, estado_admision=estado_admision,
            )
            self.db.add(estudio)
            try:
                self.db.commit()
                return estudio
            except IntegrityError:
                self.db.rollback()
        raise RuntimeError("No se pudo asignar un código anónimo")

    def agregar_archivo(self, id_estudio: int, ruta: str, tamano: int, sha256: str) -> Archivo:
        archivo = Archivo(
            id_estudio=id_estudio, ruta=ruta, tamano_bytes=tamano, hash_sha256=sha256, valido=True
        )
        self.db.add(archivo)
        return archivo

    def _consulta(self):
        return select(Estudio).options(
            selectinload(Estudio.trabajos).selectinload(Trabajo.resultado)
        )

    def listar(self, usuario: Usuario) -> list[Estudio]:
        consulta = (
            self._consulta().where(Estudio.id_usuario == usuario.id_usuario)
            .order_by(Estudio.id_estudio.desc())
        )
        return list(self.db.scalars(consulta))

    def obtener(self, id_estudio: int, usuario: Usuario) -> Estudio | None:
        consulta = self._consulta().where(
            Estudio.id_estudio == id_estudio, Estudio.id_usuario == usuario.id_usuario
        )
        return self.db.scalar(consulta)

    def archivos(self, id_estudio: int) -> list[Archivo]:
        return list(self.db.scalars(
            select(Archivo).where(Archivo.id_estudio == id_estudio).order_by(Archivo.id_archivo)
        ))

    def eliminar(self, estudio: Estudio) -> None:
        self.db.delete(estudio)
        self.db.commit()
