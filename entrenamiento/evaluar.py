"""Evaluación del modelo sobre el conjunto de PRUEBA (RF-23, RF-24).

Usa `build_pipeline`, la misma ruta que la aplicación: control de calidad,
preparación, segmentación y paso a la rejilla original; Dice e IoU se calculan
en el espacio de la imagen original contra la etiqueta (próstata = etiqueta > 0).

Uso (desde la raíz del repositorio):
    backend/.venv/bin/python -m entrenamiento.evaluar --modelo prostate_mri_anatomy
    backend/.venv/bin/python -m entrenamiento.evaluar --modelo prostate_mri_anatomy --todos

Escribe `reports/evaluacion/evaluacion_<modelo>_<fecha>.md` y `.csv`.
"""
from __future__ import annotations

import argparse
import csv
import json
import platform
import sys
import tempfile
import time
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ) not in sys.path:  # permite ejecutar también como script suelto
    sys.path.insert(0, str(RAIZ))

import monai
import numpy as np
import torch

from entrenamiento.division import DATOS_POR_DEFECTO, DIVISION_POR_DEFECTO, cargar_division, rutas_caso
from prosta_ai.pipeline.base import PipelineInput
from prosta_ai.pipeline.factory import build_pipeline, model_info
from prosta_ai.pipeline.progress import PipelineProgress

META_DICE = 0.80  # RF-24
MODELOS = RAIZ / "modelos"
INFORMES = RAIZ / "reports" / "evaluacion"


def hardware(dispositivo: str | None) -> str:
    """Descripción breve del equipo donde se mide (CPU/GPU, hilos, RAM)."""
    cpu = platform.processor() or platform.machine()
    try:  # nombre comercial de la CPU en Linux
        for linea in Path("/proc/cpuinfo").read_text().splitlines():
            if linea.startswith("model name"):
                cpu = linea.split(":", 1)[1].strip()
                break
    except OSError:
        pass
    usa_gpu = (dispositivo or ("cuda" if torch.cuda.is_available() else "cpu")).startswith("cuda")
    gpu = torch.cuda.get_device_name(0) if usa_gpu and torch.cuda.is_available() else "sin GPU (CPU)"
    return f"{cpu}; {torch.get_num_threads()} hilos de torch; {gpu}; {platform.system()} {platform.release()}"


def evaluar_casos(modelo: str, carpeta: Path, datos: Path, ids: list[str], dispositivo: str | None) -> list[dict]:
    """Ejecuta el pipeline de la aplicación en cada caso y devuelve una fila por caso."""
    pipeline = build_pipeline(modelo, carpeta)
    if dispositivo:
        pipeline.strategy._device = torch.device(dispositivo)
    filas = []
    for n, caso in enumerate(ids, 1):
        imagen, etiqueta = rutas_caso(datos, caso)
        with tempfile.TemporaryDirectory() as tmp:
            entrada = PipelineInput(files=[imagen], fmt="NIfTI", reference_files=[etiqueta], output_dir=Path(tmp))
            t0 = time.perf_counter()
            salida = pipeline.run(entrada, PipelineProgress())
            segundos = time.perf_counter() - t0
        fila = {"caso": caso, "dice": salida.dice, "iou": salida.iou, "tiempo_s": round(segundos, 1)}
        filas.append(fila)
        print(f"[{n}/{len(ids)}] {caso}: Dice={fila['dice']:.4f} IoU={fila['iou']:.4f} ({segundos:.0f} s)", flush=True)
    return filas


def resumen(filas: list[dict], clave: str) -> tuple[float, float]:
    """Media y desviación típica muestral (n-1) de una columna."""
    v = np.array([f[clave] for f in filas], dtype=float)
    return float(v.mean()), float(v.std(ddof=1)) if len(v) > 1 else 0.0


def tabla(filas: list[dict]) -> str:
    lineas = ["| Caso | Dice | IoU | Tiempo (s) |", "|---|---:|---:|---:|"]
    lineas += [f"| {f['caso']} | {f['dice']:.4f} | {f['iou']:.4f} | {f['tiempo_s']:.1f} |" for f in filas]
    dm, ds = resumen(filas, "dice")
    im, is_ = resumen(filas, "iou")
    tm, ts = resumen(filas, "tiempo_s")
    lineas.append(f"| **Media ± desv.** | **{dm:.4f} ± {ds:.4f}** | **{im:.4f} ± {is_:.4f}** | **{tm:.1f} ± {ts:.1f}** |")
    return "\n".join(lineas)


def construir_informe(modelo: str, info: dict, division: dict, filas: list[dict], todos: list[dict] | None,
                      equipo: str, dispositivo: str, sesgo: str) -> str:
    dm, ds = resumen(filas, "dice")
    cumple = dm >= META_DICE
    veredicto = (
        f"Se **cumple** la meta (Dice medio {dm:.4f} >= {META_DICE:.2f})." if cumple
        else f"**No se cumple** la meta: Dice medio {dm:.4f} < {META_DICE:.2f} (brecha de {META_DICE - dm:.4f})."
    )
    peor = min(filas, key=lambda f: f["dice"])
    md = [
        f"# Evaluación del modelo `{info['nombre']}` ({date.today().isoformat()})",
        "",
        "Uso académico y experimental; no es una evaluación clínica ni diagnóstica.",
        "",
        "## Condiciones",
        "",
        f"- Modelo: {info['nombre']}, versión {info['version']}.",
        f"- SHA-256 de los pesos: `{info['hash_pesos']}`.",
        f"- Ruta de ejecución: `build_pipeline` (la misma que la aplicación), imagen = canal 0 (T2) del NIfTI 4D, "
        "referencia = etiquetas > 0 (zona periférica + zona de transición).",
        f"- Métricas calculadas en la rejilla de la imagen original (máscara devuelta al espacio original).",
        f"- Dispositivo: {dispositivo}. Hardware: {equipo}.",
        f"- Software: Python {platform.python_version()}, torch {torch.__version__}, MONAI {monai.__version__}.",
        f"- División: `entrenamiento/division_task05.json`, semilla {division['semilla']}, "
        f"{division['cantidades']}, huella `{division['huella_sha256'][:16]}…`.",
        f"- Conjunto evaluado: prueba ({len(filas)} casos: {', '.join(f['caso'] for f in filas)}).",
        "- Tiempo por caso: todo el pipeline (lectura, preparación, segmentación, paso al espacio original), "
        "incluida la carga de los pesos, que se hace una sola vez en el primer caso.",
        "- Desviación: típica muestral (n-1).",
        "",
        "## Resultados sobre el conjunto de prueba",
        "",
        tabla(filas),
        "",
        "## Comparación con la meta (RF-24)",
        "",
        veredicto,
        f"El caso más bajo es {peor['caso']} (Dice {peor['dice']:.4f}).",
        "",
    ]
    if todos:
        md += ["## Dato adicional: los 32 casos de Task05", "", tabla(todos), ""]
    md += [
        "## Limitaciones",
        "",
        sesgo,
        "- Con solo 5 casos de prueba la media tiene mucha incertidumbre; un caso malo mueve mucho el promedio "
        "(ver la desviación típica).",
        "- Cambio de dominio: los pesos se entrenaron con Prostate158 (T2, 3 T, hospital distinto) y Task05 tiene "
        "cortes gruesos (4 mm), otra resolución y otro protocolo; el remuestreo a 0,5 mm es por interpolación y no "
        "añade detalle.",
        "- Las etiquetas de Task05 son zona periférica y de transición; la próstata completa es su unión, mientras "
        "el modelo se entrenó para dos zonas. Los criterios de delimitación de los anotadores pueden diferir "
        "(p. ej. en base y ápex).",
        "- Un solo conjunto público y un solo observador por caso (sin variabilidad entre observadores).",
        "- Las métricas de superficie (Hausdorff, etc.) no se calculan; solo Dice e IoU.",
        "- Los tiempos dependen del equipo; no representan el rendimiento en otro hardware.",
        "- No hay validación clínica ni externa a estos datos públicos.",
        "",
    ]
    return "\n".join(md)


def texto_sesgo(carpeta: Path, modelo: str) -> str:
    """Limitación obligatoria sobre el posible solapamiento entre datos de entrenamiento y Task05."""
    meta_p = carpeta / "configs" / "metadata.json"
    readme = carpeta / "docs" / "README.md"
    if meta_p.exists():
        fuente = json.loads(meta_p.read_text(encoding="utf-8")).get("data_source", "")
        return (
            "- **Posible sesgo (sobreestimación) por datos de entrenamiento.** Según la documentación del bundle "
            f"(`configs/metadata.json`, campo `data_source`: \"{fuente}\"; `docs/README.md`: \"The model was trained in "
            "the prostate158 training data ... Only T2w images were used for this task\"), el modelo preentrenado "
            "se entrenó con Prostate158 y la documentación no menciona MSD Task05 ni como entrenamiento ni como "
            "validación. Por tanto no hay evidencia documentada de solapamiento, pero tampoco se puede garantizar "
            "que los datos de Task05 estén ausentes de su preentrenamiento ni de la fuente de Prostate158 (el bundle "
            "no incluye la lista de casos ni las semillas). Si hubiera solapamiento, la evaluación sobre Task05 "
            "estaría sobreestimada. Además, la división 70/15/15 de este proyecto es independiente de cualquier "
            "división usada por los autores del bundle, así que los casos de prueba de aquí no son, por "
            "construcción, 'no vistos' por ese modelo. Las cifras del propio bundle (Dice de glándula central 0,88 y "
            "zona periférica 0,75) son sobre el conjunto de prueba de Prostate158, no de Task05."
        )
    return (
        "- **Posible sesgo (sobreestimación).** Si el modelo se entrenó o ajustó con datos que incluyen casos "
        "de prueba, la evaluación está sobreestimada; revise `metadatos.json` y la división del modelo."
    )


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--modelo", default="prostate_mri_anatomy", help="Nombre de la carpeta en --directorio-modelos.")
    ap.add_argument("--directorio-modelos", type=Path, default=MODELOS)
    ap.add_argument("--datos", type=Path, default=DATOS_POR_DEFECTO)
    ap.add_argument("--division", type=Path, default=DIVISION_POR_DEFECTO)
    ap.add_argument("--dispositivo", default=None, help="cpu o cuda (por defecto lo elige la aplicación).")
    ap.add_argument("--todos", action="store_true", help="Evalúa además los 32 casos como dato adicional.")
    ap.add_argument("--salida", type=Path, default=INFORMES)
    ap.add_argument("--limite", type=int, default=None, help="Solo los N primeros casos (pruebas).")
    args = ap.parse_args()

    carpeta = args.directorio_modelos / args.modelo
    # build_pipeline reconoce por nombre solo el bundle; un modelo propio entra como "unet" + su carpeta
    nombre_estrategia = args.modelo if args.modelo == "prostate_mri_anatomy" else "unet"
    info = model_info(nombre_estrategia, carpeta)
    division = cargar_division(args.division)
    conj = division["conjuntos"]
    ids_prueba = conj["prueba"][: args.limite]
    filas = evaluar_casos(nombre_estrategia, carpeta, args.datos, ids_prueba, args.dispositivo)

    todos = None
    if args.todos:
        resto = [c for k in ("entrenamiento", "validacion", "prueba") for c in conj[k]]
        previos = {f["caso"]: f for f in filas}
        extra = evaluar_casos(nombre_estrategia, carpeta, args.datos, [c for c in sorted(resto) if c not in previos],
                              args.dispositivo)
        todos = sorted(filas + extra, key=lambda f: f["caso"])

    dispositivo = args.dispositivo or ("cuda" if torch.cuda.is_available() else "cpu")
    informe = construir_informe(args.modelo, info, division, filas, todos, hardware(args.dispositivo), dispositivo,
                                texto_sesgo(carpeta, args.modelo))
    args.salida.mkdir(parents=True, exist_ok=True)
    base = f"evaluacion_{args.modelo}_{date.today().isoformat()}" + ("_32casos" if args.todos else "")
    (args.salida / f"{base}.md").write_text(informe, encoding="utf-8")
    pertenece = {c: k for k, v in conj.items() for c in v}
    with open(args.salida / f"{base}.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["caso", "conjunto", "dice", "iou", "tiempo_s"])
        for fila in todos or filas:
            w.writerow([fila["caso"], pertenece[fila["caso"]], f"{fila['dice']:.6f}", f"{fila['iou']:.6f}", fila["tiempo_s"]])
    print(f"Informe escrito en {args.salida / (base + '.md')}")


if __name__ == "__main__":
    main()
