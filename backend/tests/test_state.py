import pytest

from prosta_ai.jobs.state import (
    CompletedState, FailedState, InProgressState, InvalidTransition, Job, PendingState,
)


def test_flujo_completado():
    job = Job()
    assert job.estado == "pendiente" and isinstance(job._state, PendingState)
    job.iniciar()
    assert job.estado == "en proceso" and isinstance(job._state, InProgressState)
    job.completar()
    assert job.estado == "completado" and isinstance(job._state, CompletedState)


def test_flujo_fallido():
    job = Job("pendiente")
    job.iniciar()
    job.fallar()
    assert job.estado == "fallido" and isinstance(job._state, FailedState)


@pytest.mark.parametrize("inicial,accion", [
    ("pendiente", "completar"), ("pendiente", "fallar"), ("pendiente", "iniciar_dos"),
    ("en proceso", "iniciar"), ("completado", "iniciar"), ("completado", "fallar"),
    ("completado", "completar"), ("fallido", "iniciar"), ("fallido", "completar"),
])
def test_transiciones_invalidas(inicial, accion):
    job = Job(inicial)
    if accion == "iniciar_dos":
        job.iniciar()
        accion = "iniciar"
    with pytest.raises(InvalidTransition):
        getattr(job, accion)()


def test_estado_desconocido():
    with pytest.raises(ValueError):
        Job("otro")
