"""Patrón State del trabajo: pendiente -> en proceso -> completado | fallido."""
from abc import ABC


class InvalidTransition(Exception):
    """Transición de estado no permitida."""


class JobState(ABC):
    nombre: str

    def iniciar(self, job: "Job") -> None:
        self._invalida(job, "en proceso")

    def completar(self, job: "Job") -> None:
        self._invalida(job, "completado")

    def fallar(self, job: "Job") -> None:
        self._invalida(job, "fallido")

    def _invalida(self, job: "Job", destino: str) -> None:
        raise InvalidTransition(f"No se puede pasar de '{self.nombre}' a '{destino}'")


class PendingState(JobState):
    nombre = "pendiente"

    def iniciar(self, job: "Job") -> None:
        job._cambiar(InProgressState())


class InProgressState(JobState):
    nombre = "en proceso"

    def completar(self, job: "Job") -> None:
        job._cambiar(CompletedState())

    def fallar(self, job: "Job") -> None:
        job._cambiar(FailedState())


class CompletedState(JobState):
    nombre = "completado"


class FailedState(JobState):
    nombre = "fallido"


_ESTADOS = {e.nombre: e for e in (PendingState, InProgressState, CompletedState, FailedState)}


class Job:
    """Contexto del patrón: aplica las transiciones sobre el estado actual."""

    def __init__(self, estado: str = "pendiente"):
        if estado not in _ESTADOS:
            raise ValueError(f"Estado desconocido: {estado}")
        self._state: JobState = _ESTADOS[estado]()

    @property
    def estado(self) -> str:
        return self._state.nombre

    def _cambiar(self, nuevo: JobState) -> None:
        self._state = nuevo

    def iniciar(self) -> None:
        self._state.iniciar(self)

    def completar(self) -> None:
        self._state.completar(self)

    def fallar(self) -> None:
        self._state.fallar(self)
