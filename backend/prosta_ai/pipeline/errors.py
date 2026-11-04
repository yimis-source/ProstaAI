"""Errores controlados del pipeline."""


class AdmissionError(Exception):
    """Rechazo de un archivo en la carga (formato o tamaño)."""

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class StageError(Exception):
    """Fallo controlado de una etapa del procesamiento."""

    def __init__(self, stage: str, message: str):
        super().__init__(f"{stage}: {message}")
        self.stage = stage
        self.message = message
