import hashlib

import sqlalchemy as sa
from sqlalchemy import select

from prosta_ai.db import Base
import prosta_ai.models  # noqa: F401
from prosta_ai.models import Archivo

PROHIBIDAS = ("nombre", "apellido", "correo", "email", "telefono", "documento", "cedula",
              "direccion", "edad", "nacimiento", "paciente", "genero", "sexo")


def test_esquema_sin_columnas_personales():
    for tabla in Base.metadata.tables.values():
        for col in tabla.columns:
            if tabla.name == "modelo" and col.name == "nombre":
                continue  # nombre del modelo de IA, no de personas
            if tabla.name == "etapa_trabajo" and col.name == "nombre":
                continue  # nombre de la etapa
            assert not any(p in col.name.lower() for p in PROHIBIDAS), f"{tabla.name}.{col.name}"


def test_nombres_guardados_son_neutros(entorno):
    cab = entorno.cabeceras()
    r = entorno.cargar(cab, nombre="Juan_Perez_1980-05-03.nii.gz", referencia=True)
    assert r.status_code == 201
    with entorno.app.state.session_factory() as s:
        archivos = list(s.scalars(select(Archivo)))
    assert len(archivos) == 2
    rutas = sorted(a.ruta for a in archivos)
    assert rutas == ["estudios/EST-0001/imagen/archivo_001.nii.gz",
                     "estudios/EST-0001/referencia/referencia_001.nii.gz"]
    for a in archivos:
        assert "juan" not in a.ruta.lower() and "perez" not in a.ruta.lower() and "maria" not in a.ruta.lower()
        guardado = entorno.settings.storage_dir / a.ruta
        assert guardado.stat().st_size == a.tamano_bytes
        assert hashlib.sha256(guardado.read_bytes()).hexdigest() == a.hash_sha256
        assert a.valido is True
    # nada en el árbol de almacenamiento conserva el nombre original
    todos = [p.name.lower() for p in entorno.settings.storage_dir.rglob("*")]
    assert not any("juan" in n or "perez" in n for n in todos)


def test_extension_desconocida_se_neutraliza():
    from prosta_ai.storage import extension_segura

    assert extension_segura("Maria Lopez.PDF") == ".bin"
    assert extension_segura("x.NII.GZ") == ".nii.gz"
    assert extension_segura("serie.dcm") == ".dcm"
