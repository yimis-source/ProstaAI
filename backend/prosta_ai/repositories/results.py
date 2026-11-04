from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from prosta_ai.models import Resultado


class ResultRepository:
    def __init__(self, db: Session):
        self.db = db

    def crear(
        self, id_trabajo: int, ruta_mascara: str, dice: float | None, iou: float | None,
        tiempo_total_s: float,
    ) -> Resultado:
        resultado = Resultado(
            id_trabajo=id_trabajo, ruta_mascara=ruta_mascara,
            dice=None if dice is None else Decimal(str(round(dice, 3))),
            iou=None if iou is None else Decimal(str(round(iou, 3))),
            tiempo_total_s=Decimal(str(round(tiempo_total_s, 2))),
        )
        self.db.add(resultado)
        return resultado

    def del_trabajo(self, id_trabajo: int) -> Resultado | None:
        return self.db.scalar(select(Resultado).where(Resultado.id_trabajo == id_trabajo))
