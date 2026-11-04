"""ProcessingWorker: hilo que toma los trabajos pendientes de uno en uno."""
import logging
import threading

from prosta_ai.processing.service import ProcessingService

log = logging.getLogger(__name__)


class ProcessingWorker:
    def __init__(self, service: ProcessingService, intervalo_s: float = 2.0):
        self._service = service
        self._intervalo = intervalo_s
        self._parar = threading.Event()
        self._hilo: threading.Thread | None = None

    def process_next(self) -> bool:
        """Procesa un trabajo pendiente si hay; devuelve False cuando no había ninguno."""
        return self._service.ejecutar_siguiente()

    def _bucle(self) -> None:
        while not self._parar.is_set():
            try:
                hubo_trabajo = self.process_next()
            except Exception:
                log.exception("Fallo del worker al tomar un trabajo")
                hubo_trabajo = False
            if not hubo_trabajo:
                self._parar.wait(self._intervalo)

    def start(self) -> None:
        if self._hilo and self._hilo.is_alive():
            return
        self._parar.clear()
        self._hilo = threading.Thread(target=self._bucle, name="prosta-worker", daemon=True)
        self._hilo.start()

    def stop(self) -> None:
        self._parar.set()
        if self._hilo:
            self._hilo.join(timeout=5)
