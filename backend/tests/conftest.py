import gzip
from types import SimpleNamespace

import nibabel as nib
import numpy as np
import pytest
from fastapi.testclient import TestClient

from prosta_ai import security
from prosta_ai.api.app import create_app
from prosta_ai.config import Settings
from prosta_ai.db import Base
from prosta_ai.pipeline.errors import AdmissionError, StageError
from prosta_ai.pipeline.stages import STAGES

security.ROUNDS = 4  # bcrypt más rápido en pruebas


from apoyo_api import PipelineFalso, admision_falsa, nifti_gz  # noqa: E402


class Entorno:
    def __init__(self, tmp_path, pipeline):
        self.settings = Settings(
            database_url=f"sqlite:///{tmp_path / 'prueba.db'}", storage_dir=tmp_path / "almacen",
            secret_key="clave-de-pruebas", worker_activo=False, max_upload_mb=1,
        )
        self.pipeline = pipeline
        self.app = create_app(
            self.settings, pipeline_provider=lambda: self.pipeline, admission=admision_falsa,
            model_info_fn=lambda s: {"nombre": "modelo_prueba", "version": "1"},
        )
        Base.metadata.create_all(self.app.state.engine)
        self.client = TestClient(self.app)
        self.client.__enter__()

    def cabeceras(self, alias="ana", contrasena="clave-segura-1") -> dict:
        r = self.client.post(
            "/api/acceso", json={"alias": alias, "contrasena": contrasena, "confirmacion": contrasena}
        )
        if r.status_code != 200:  # el alias ya existía
            r = self.client.post("/api/acceso", json={"alias": alias, "contrasena": contrasena})
        return {"Authorization": f"Bearer {r.json()['token']}"}

    def cargar(self, cab, nombre="paciente_juan_perez.nii.gz", contenido=None, referencia=False):
        archivos = [("archivos", (nombre, contenido or nifti_gz(), "application/gzip"))]
        if referencia:
            archivos.append(("referencia", ("ref_maria.nii.gz", nifti_gz(), "application/gzip")))
        return self.client.post("/api/estudios", files=archivos, headers=cab)

    def procesar(self, cab, id_estudio):
        return self.client.post(f"/api/estudios/{id_estudio}/procesar", headers=cab)

    def worker(self):
        return self.app.state.worker

    def cerrar(self):
        self.client.__exit__(None, None, None)


@pytest.fixture
def entorno(tmp_path):
    e = Entorno(tmp_path, PipelineFalso())
    yield e
    e.cerrar()
