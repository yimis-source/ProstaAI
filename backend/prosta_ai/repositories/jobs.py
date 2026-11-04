from sqlalchemy import select
from sqlalchemy.orm import Session

from prosta_ai.constantes import EN_PROCESO, PENDIENTE
from prosta_ai.models import EtapaTrabajo, Estudio, Trabajo, Usuario


class JobRepository:
    def __init__(self, db: Session):
        self.db = db

    def crear(self, id_estudio: int, id_modelo: int) -> Trabajo:
        trabajo = Trabajo(id_estudio=id_estudio, id_modelo=id_modelo, estado=PENDIENTE)
        self.db.add(trabajo)
        self.db.commit()
        return trabajo

    def obtener(self, id_trabajo: int) -> Trabajo | None:
        return self.db.get(Trabajo, id_trabajo)

    def obtener_de_usuario(self, id_trabajo: int, usuario: Usuario) -> Trabajo | None:
        consulta = (
            select(Trabajo).join(Estudio, Estudio.id_estudio == Trabajo.id_estudio)
            .where(Trabajo.id_trabajo == id_trabajo, Estudio.id_usuario == usuario.id_usuario)
        )
        return self.db.scalar(consulta)

    def activo_del_estudio(self, id_estudio: int) -> Trabajo | None:
        consulta = select(Trabajo).where(
            Trabajo.id_estudio == id_estudio, Trabajo.estado.in_([PENDIENTE, EN_PROCESO])
        )
        return self.db.scalars(consulta).first()

    def reclamar_siguiente_pendiente(self) -> Trabajo | None:
        """Toma el pendiente más antiguo; en PostgreSQL con SKIP LOCKED."""
        consulta = (
            select(Trabajo).where(Trabajo.estado == PENDIENTE)
            .order_by(Trabajo.id_trabajo).limit(1)
        )
        if self.db.get_bind().dialect.name == "postgresql":
            consulta = consulta.with_for_update(skip_locked=True)
        return self.db.scalar(consulta)

    def en_proceso(self) -> list[Trabajo]:
        return list(self.db.scalars(select(Trabajo).where(Trabajo.estado == EN_PROCESO)))

    def crear_etapas(self, id_trabajo: int, nombres: list[str]) -> None:
        for nombre in nombres:
            self.db.add(EtapaTrabajo(id_trabajo=id_trabajo, nombre=nombre, estado=PENDIENTE))

    def etapas(self, id_trabajo: int) -> list[EtapaTrabajo]:
        return list(self.db.scalars(
            select(EtapaTrabajo).where(EtapaTrabajo.id_trabajo == id_trabajo)
            .order_by(EtapaTrabajo.id_etapa)
        ))
