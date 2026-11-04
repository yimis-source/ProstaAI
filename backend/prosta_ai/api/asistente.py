"""CU06: asistente de orientación sobre el uso de la aplicación."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from prosta_ai.api.deps import get_db, usuario_actual
from prosta_ai.api.schemas import PreguntaEntrada
from prosta_ai.assistant import ContextoUsuario, responder
from prosta_ai.models import Usuario

router = APIRouter(prefix="/asistente", tags=["asistente"])


@router.post("")
def preguntar(
    datos: PreguntaEntrada, usuario: Usuario = Depends(usuario_actual), db: Session = Depends(get_db)
):
    return responder(datos.pregunta, ContextoUsuario(db, usuario))
