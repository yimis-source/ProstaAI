"""División por paciente en entrenamiento, validación y prueba (RC-04).

Cada caso del Medical Segmentation Decathlon Task05 es un paciente distinto
(el conjunto no trae un identificador de paciente aparte), así que dividir por
caso equivale a dividir por paciente.

Uso (desde la raíz del repositorio):
    backend/.venv/bin/python -m entrenamiento.division
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ) not in sys.path:  # permite ejecutar también como script suelto
    sys.path.insert(0, str(RAIZ))

SEMILLA = 2026
PROPORCIONES = {"entrenamiento": 0.70, "validacion": 0.15, "prueba": 0.15}
CONJUNTOS = tuple(PROPORCIONES)
DATOS_POR_DEFECTO = RAIZ / "datos" / "Task05_Prostate"
DIVISION_POR_DEFECTO = RAIZ / "entrenamiento" / "division_task05.json"


def listar_casos(datos: Path) -> list[str]:
    """Identificadores (p. ej. `prostate_00`) con imagen y etiqueta en `imagesTr`/`labelsTr`."""
    datos = Path(datos)
    ids = []
    for img in sorted((datos / "imagesTr").glob("*.nii.gz")):
        if img.name.startswith("."):  # restos de macOS (._archivo)
            continue
        caso = img.name[: -len(".nii.gz")]
        if (datos / "labelsTr" / img.name).is_file():
            ids.append(caso)
    return ids


def rutas_caso(datos: Path, caso: str) -> tuple[Path, Path]:
    """(imagen, etiqueta) de un caso."""
    datos = Path(datos)
    return datos / "imagesTr" / f"{caso}.nii.gz", datos / "labelsTr" / f"{caso}.nii.gz"


def dividir(casos: list[str], semilla: int = SEMILLA) -> dict[str, list[str]]:
    """Reparte los casos 70/15/15 de forma reproducible (mezcla con semilla fija)."""
    unicos = sorted(set(casos))
    n = len(unicos)
    if n < 3:
        raise ValueError("Se necesitan al menos 3 casos para dividir en tres conjuntos.")
    mezclados = unicos[:]
    random.Random(semilla).shuffle(mezclados)
    n_val = max(1, round(n * PROPORCIONES["validacion"]))
    n_prueba = max(1, round(n * PROPORCIONES["prueba"]))
    n_entr = n - n_val - n_prueba
    return {
        "entrenamiento": sorted(mezclados[:n_entr]),
        "validacion": sorted(mezclados[n_entr : n_entr + n_val]),
        "prueba": sorted(mezclados[n_entr + n_val :]),
    }


def verificar_division(conjuntos: dict[str, list[str]], esperados: list[str] | None = None) -> None:
    """Lanza ValueError si hay pacientes repetidos o faltan/sobran casos (RC-04)."""
    if set(conjuntos) != set(CONJUNTOS):
        raise ValueError(f"La división debe tener los conjuntos {CONJUNTOS}.")
    vistos: dict[str, str] = {}
    for nombre in CONJUNTOS:
        lista = conjuntos[nombre]
        if len(lista) != len(set(lista)):
            raise ValueError(f"Hay casos repetidos dentro del conjunto '{nombre}'.")
        if not lista:
            raise ValueError(f"El conjunto '{nombre}' está vacío.")
        for caso in lista:
            if caso in vistos:
                raise ValueError(f"El paciente {caso} está en '{vistos[caso]}' y en '{nombre}'.")
            vistos[caso] = nombre
    if esperados is not None and set(vistos) != set(esperados):
        raise ValueError("La división no cubre exactamente los casos disponibles.")


def huella(conjuntos: dict[str, list[str]]) -> str:
    """SHA-256 del contenido de la división (para trazarla en los metadatos del modelo)."""
    texto = json.dumps({k: sorted(conjuntos[k]) for k in CONJUNTOS}, sort_keys=True)
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def crear_division(datos: Path, salida: Path, semilla: int = SEMILLA) -> dict:
    """Divide, verifica y escribe el JSON. Devuelve el diccionario escrito."""
    casos = listar_casos(datos)
    conjuntos = dividir(casos, semilla)
    verificar_division(conjuntos, casos)
    doc = {
        "fuente": "Medical Segmentation Decathlon, Task05_Prostate (imagesTr/labelsTr)",
        "criterio": "un caso = un paciente; sin pacientes repetidos entre conjuntos",
        "semilla": semilla,
        "proporciones": PROPORCIONES,
        "fecha": date.today().isoformat(),
        "total_casos": len(casos),
        "cantidades": {k: len(v) for k, v in conjuntos.items()},
        "huella_sha256": huella(conjuntos),
        "conjuntos": conjuntos,
    }
    salida = Path(salida)
    salida.parent.mkdir(parents=True, exist_ok=True)
    salida.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return doc


def cargar_division(ruta: Path) -> dict:
    """Lee una división guardada y la verifica antes de devolverla."""
    doc = json.loads(Path(ruta).read_text(encoding="utf-8"))
    verificar_division(doc["conjuntos"])
    if doc.get("huella_sha256") != huella(doc["conjuntos"]):
        raise ValueError("La huella de la división no coincide: el archivo fue modificado.")
    return doc


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--datos", type=Path, default=DATOS_POR_DEFECTO)
    ap.add_argument("--salida", type=Path, default=DIVISION_POR_DEFECTO)
    ap.add_argument("--semilla", type=int, default=SEMILLA)
    args = ap.parse_args()
    doc = crear_division(args.datos, args.salida, args.semilla)
    print(f"División escrita en {args.salida}: {doc['cantidades']} (total {doc['total_casos']}).")
    print("Verificación RC-04: sin pacientes repetidos entre conjuntos.")


if __name__ == "__main__":
    main()
