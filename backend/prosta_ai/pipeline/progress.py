"""Notificación de avance del pipeline (patrón Observer)."""
from __future__ import annotations

from typing import Protocol


class PipelineObserver(Protocol):
    """Quien quiera enterarse del avance implementa estos tres métodos."""

    def on_stage_start(self, stage: str) -> None: ...

    def on_stage_end(self, stage: str, duration_s: float) -> None: ...

    def on_stage_failed(self, stage: str, message: str) -> None: ...


class PipelineProgress:
    """Sujeto del patrón Observer: reparte los eventos a los observadores."""

    def __init__(self) -> None:
        self._observers: list[PipelineObserver] = []

    def attach(self, observer: PipelineObserver) -> None:
        if observer not in self._observers:
            self._observers.append(observer)

    def notify_start(self, stage: str) -> None:
        for obs in list(self._observers):
            obs.on_stage_start(stage)

    def notify_end(self, stage: str, duration_s: float) -> None:
        for obs in list(self._observers):
            obs.on_stage_end(stage, duration_s)

    def notify_failed(self, stage: str, message: str) -> None:
        for obs in list(self._observers):
            obs.on_stage_failed(stage, message)


class TimingRecorder:
    """Observador que guarda la duración (segundos) de cada etapa terminada."""

    def __init__(self) -> None:
        self.durations: dict[str, float] = {}

    def on_stage_start(self, stage: str) -> None:
        pass

    def on_stage_end(self, stage: str, duration_s: float) -> None:
        self.durations[stage] = duration_s

    def on_stage_failed(self, stage: str, message: str) -> None:
        pass
