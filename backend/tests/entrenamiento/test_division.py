import json

import pytest

from entrenamiento.division import (
    CONJUNTOS,
    cargar_division,
    crear_division,
    dividir,
    listar_casos,
    verificar_division,
)

CASOS = [f"prostate_{i:02d}" for i in range(32)]


def test_division_70_15_15_sin_repetidos():
    d = dividir(CASOS)
    assert {k: len(v) for k, v in d.items()} == {"entrenamiento": 22, "validacion": 5, "prueba": 5}
    verificar_division(d, CASOS)
    todos = [c for k in CONJUNTOS for c in d[k]]
    assert len(todos) == len(set(todos)) == 32


def test_division_reproducible_y_depende_de_la_semilla():
    assert dividir(CASOS) == dividir(list(reversed(CASOS)))
    assert dividir(CASOS, semilla=1) != dividir(CASOS, semilla=2)


def test_verificar_detecta_paciente_repetido():
    d = dividir(CASOS)
    d["prueba"].append(d["entrenamiento"][0])
    with pytest.raises(ValueError, match="está en"):
        verificar_division(d)


def test_verificar_detecta_casos_que_faltan():
    d = dividir(CASOS)
    d["prueba"].pop()
    with pytest.raises(ValueError):
        verificar_division(d, CASOS)


def test_crear_y_cargar_division(tmp_path):
    for sub in ("imagesTr", "labelsTr"):
        (tmp_path / sub).mkdir()
        for c in CASOS[:10]:
            (tmp_path / sub / f"{c}.nii.gz").write_bytes(b"x")
    (tmp_path / "imagesTr" / "._basura.nii.gz").write_bytes(b"x")  # se ignora
    assert listar_casos(tmp_path) == CASOS[:10]
    salida = tmp_path / "div.json"
    doc = crear_division(tmp_path, salida)
    assert cargar_division(salida)["huella_sha256"] == doc["huella_sha256"]
    # si alguien edita el archivo, la huella lo delata
    contenido = json.loads(salida.read_text())
    contenido["conjuntos"]["prueba"], contenido["conjuntos"]["validacion"] = (
        contenido["conjuntos"]["validacion"],
        contenido["conjuntos"]["prueba"],
    )
    salida.write_text(json.dumps(contenido))
    with pytest.raises(ValueError, match="huella"):
        cargar_division(salida)
