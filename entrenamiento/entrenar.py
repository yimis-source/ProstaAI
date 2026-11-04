"""Entrenamiento / ajuste fino de la UNet 3D de Prosta-AI con MONAI.

La preparación del volumen (orientación, espaciado, escala y normalización de
intensidad) es EXACTAMENTE la de la inferencia: se importa
`prosta_ai.pipeline.preparation` y se lee la misma `preparacion.json` (RF-09).

Por defecto se parte de los pesos del bundle `prostate_mri_anatomy` (ajuste
fino). Con `--desde-cero` se inicializa la red al azar con la misma arquitectura.

Uso (desde la raíz del repositorio):
    backend/.venv/bin/python -m entrenamiento.entrenar --max-epocas 100 --dispositivo cuda
    backend/.venv/bin/python -m entrenamiento.entrenar --prueba-rapida   # comprobación en CPU

Resultado: carpeta `modelos/<nombre>/` con `models/model.pt`, `preparacion.json`,
`metadatos.json`, `division.json`, `historial.json` y `FICHA.md`, lista para
`create_strategy` / `build_pipeline`.
"""
from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import platform
import random
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ) not in sys.path:  # permite ejecutar también como script suelto
    sys.path.insert(0, str(RAIZ))

import monai
import numpy as np
import torch
from monai.data import MetaTensor
from monai.inferers import SlidingWindowInferer
from monai.losses import DiceCELoss
from monai.networks.nets import UNet
from monai.transforms import (
    Compose,
    Orientationd,
    RandCropByPosNegLabeld,
    RandFlipd,
    RandScaleIntensityd,
    RandShiftIntensityd,
    SpatialPadd,
    Spacingd,
)
from monai.utils import set_determinism

from entrenamiento.division import (
    DATOS_POR_DEFECTO,
    DIVISION_POR_DEFECTO,
    SEMILLA,
    cargar_division,
    crear_division,
    rutas_caso,
)
from prosta_ai.pipeline.evaluation import dice
from prosta_ai.pipeline.io import load_volume
from prosta_ai.pipeline.preparation import PreparationConfig, prepare_volume

BASE_POR_DEFECTO = RAIZ / "modelos" / "prostate_mri_anatomy"
MODELOS = RAIZ / "modelos"


# ------------------------------------------------------------------ datos

def preparar_etiqueta(ruta: Path, cfg: PreparationConfig) -> torch.Tensor:
    """Lleva la etiqueta al mismo espacio preparado que la imagen (vecino más cercano).

    MSD Task05 usa 1 = zona periférica y 2 = zona de transición; el modelo base
    usa 1 = glándula central y 2 = zona periférica. Se intercambian para que el
    ajuste fino sea coherente con los pesos de partida. La próstata completa
    sigue siendo la unión de las etiquetas > 0.
    """
    vol = load_volume([ruta], "NIfTI")
    msd = np.rint(vol.data).astype(np.int16)
    mapeada = np.zeros(msd.shape, dtype=np.float32)
    mapeada[msd == 1] = 2
    mapeada[msd == 2] = 1
    img = MetaTensor(torch.from_numpy(mapeada[None]), affine=torch.as_tensor(vol.affine, dtype=torch.float64))
    pasos = Compose(
        [
            Orientationd(keys="label", axcodes=cfg.orientacion),
            Spacingd(keys="label", pixdim=cfg.espaciado, mode="nearest"),
        ]
    )
    return torch.as_tensor(pasos({"label": img})["label"]).long().contiguous()


def preparar_caso(datos: Path, caso: str, cfg: PreparationConfig) -> dict:
    """Imagen (misma función que la inferencia) y etiqueta preparadas de un caso."""
    ruta_img, ruta_lbl = rutas_caso(datos, caso)
    imagen = prepare_volume(load_volume([ruta_img], "NIfTI"), cfg).tensor
    etiqueta = preparar_etiqueta(ruta_lbl, cfg)
    if tuple(etiqueta.shape) != tuple(imagen.shape):
        raise RuntimeError(f"{caso}: imagen {tuple(imagen.shape)} y etiqueta {tuple(etiqueta.shape)} no coinciden.")
    return {"image": imagen, "label": etiqueta}


def transformaciones_entrenamiento(cfg: PreparationConfig, crops: int) -> Compose:
    """Recortes aleatorios del tamaño de la ventana y aumentos suaves."""
    roi = list(cfg.roi_size)
    return Compose(
        [
            SpatialPadd(keys=["image", "label"], spatial_size=roi),
            RandCropByPosNegLabeld(
                keys=["image", "label"], label_key="label", spatial_size=roi, pos=1, neg=1, num_samples=crops
            ),
            RandFlipd(keys=["image", "label"], prob=0.5, spatial_axis=0),
            RandScaleIntensityd(keys="image", factors=0.1, prob=0.3),
            RandShiftIntensityd(keys="image", offsets=0.1, prob=0.3),
        ]
    )


# ------------------------------------------------------------------ red

def crear_red(cfg: PreparationConfig, pesos_base: Path | None, dispositivo: torch.device) -> torch.nn.Module:
    red = UNet(**cfg.red)
    if pesos_base is not None:
        estado = torch.load(pesos_base, map_location="cpu", weights_only=True)
        if isinstance(estado, dict) and "model" in estado:
            estado = estado["model"]
        red.load_state_dict(estado)
    return red.to(dispositivo)


@torch.no_grad()
def validar(red: torch.nn.Module, casos: list[dict], cfg: PreparationConfig, dispositivo: torch.device) -> float:
    """Dice medio de la próstata completa (unión de etiquetas > 0) en el espacio preparado."""
    red.eval()
    inferer = SlidingWindowInferer(roi_size=cfg.roi_size, sw_batch_size=cfg.sw_batch_size, overlap=cfg.overlap)
    valores = []
    for c in casos:
        logits = inferer(c["image"][None].to(dispositivo), red)
        pred = logits.argmax(dim=1)[0].cpu().numpy() > 0
        valores.append(dice(pred, c["label"][0].numpy() > 0))
    return float(np.mean(valores))


# ------------------------------------------------------------------ utilidades

def sha256(ruta: Path) -> str:
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def elegir_dispositivo(texto: str) -> torch.device:
    if texto == "auto":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if texto.startswith("cuda") and not torch.cuda.is_available():
        raise SystemExit("Se pidió CUDA pero no hay GPU disponible (en Colab: Entorno de ejecución > Cambiar tipo > GPU).")
    return torch.device(texto)


def fijar_semillas(semilla: int) -> None:
    random.seed(semilla)
    np.random.seed(semilla)
    torch.manual_seed(semilla)
    set_determinism(seed=semilla)


def escribir_salida(
    carpeta: Path, red: torch.nn.Module, cfg: PreparationConfig, args: argparse.Namespace,
    division: dict, historial: list[dict], mejor: dict, dispositivo: torch.device, segundos: float,
) -> None:
    """Escribe la carpeta del modelo compatible con `create_strategy`."""
    (carpeta / "models").mkdir(parents=True, exist_ok=True)
    pesos = carpeta / cfg.pesos
    torch.save({k: v.cpu() for k, v in red.state_dict().items()}, pesos)
    (carpeta / "preparacion.json").write_text(json.dumps(config_a_json(cfg), indent=2) + "\n", encoding="utf-8")
    shutil.copy(args.division, carpeta / "division.json")
    (carpeta / "historial.json").write_text(json.dumps(historial, indent=2) + "\n", encoding="utf-8")
    meta = {
        "nombre": cfg.nombre,
        "version": cfg.version,
        "fecha": datetime.now().isoformat(timespec="seconds"),
        "hash_pesos_sha256": sha256(pesos),
        "punto_de_partida": "aleatorio" if args.desde_cero else f"ajuste fino desde {args.base.name} (v{args.version_base})",
        "semilla": args.semilla,
        "hiperparametros": {
            "max_epocas": args.max_epocas, "tasa_aprendizaje": args.lr, "tamano_lote": args.lote,
            "recortes_por_caso": args.recortes, "validar_cada": args.validar_cada,
            "perdida": "DiceCELoss", "optimizador": "AdamW",
        },
        "mejor_epoca": mejor["epoca"],
        "mejor_dice_validacion": mejor["dice"],
        "division": {
            "archivo": "division.json", "semilla": division["semilla"], "huella_sha256": division["huella_sha256"],
            "cantidades": division["cantidades"],
        },
        "entorno": {
            "dispositivo": str(dispositivo), "python": platform.python_version(),
            "torch": torch.__version__, "monai": monai.__version__,
        },
        "duracion_entrenamiento_s": round(segundos, 1),
        "prueba_rapida": bool(args.prueba_rapida),
        "aviso": "Uso académico y experimental. No apto para diagnóstico.",
    }
    (carpeta / "metadatos.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (carpeta / "FICHA.md").write_text(
        f"# Ficha del modelo: {cfg.nombre}\n\n"
        f"- Versión: {cfg.version}\n- Fecha: {meta['fecha']}\n- Punto de partida: {meta['punto_de_partida']}\n"
        f"- Datos: MSD Task05_Prostate (CC-BY-SA 4.0), división {division['huella_sha256'][:12]}… "
        f"({division['cantidades']})\n- SHA-256 de los pesos: {meta['hash_pesos_sha256']}\n"
        f"- Mejor Dice de validación: {mejor['dice']:.4f} (época {mejor['epoca']})\n\n"
        "El modelo base procede del bundle `prostate_mri_anatomy` (Apache 2.0, Keno Bressem; "
        "ver la ficha de ese modelo).\n\n## Aviso\n\nUso académico y experimental. No apto para diagnóstico.\n",
        encoding="utf-8",
    )


def config_a_json(cfg: PreparationConfig) -> dict:
    return {
        "nombre": cfg.nombre, "version": cfg.version, "pesos": cfg.pesos,
        "orientacion": cfg.orientacion, "espaciado": list(cfg.espaciado),
        "modo_remuestreo": cfg.modo_remuestreo,
        "escala_intensidad": {"min": cfg.escala_min, "max": cfg.escala_max},
        "normalizar_intensidad": cfg.normalizar_intensidad,
        "roi_size": list(cfg.roi_size), "sw_batch_size": cfg.sw_batch_size, "overlap": cfg.overlap,
        "red": cfg.red, "etiquetas_prostata": list(cfg.etiquetas_prostata),
        "conservar_mayor_componente": cfg.conservar_mayor_componente,
    }


# ------------------------------------------------------------------ principal

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--datos", type=Path, default=DATOS_POR_DEFECTO)
    ap.add_argument("--division", type=Path, default=DIVISION_POR_DEFECTO)
    ap.add_argument("--base", type=Path, default=BASE_POR_DEFECTO, help="Carpeta del modelo de partida.")
    ap.add_argument("--desde-cero", action="store_true", help="No cargar los pesos del modelo base.")
    ap.add_argument("--nombre", default="prostate_task05_ft")
    ap.add_argument("--version", default="1.0.0")
    ap.add_argument("--salida", type=Path, default=MODELOS, help="Carpeta que contendrá modelos/<nombre>/.")
    ap.add_argument("--max-epocas", type=int, default=100)
    ap.add_argument("--dispositivo", default="auto", help="auto, cpu o cuda.")
    ap.add_argument("--lr", type=float, default=1e-4)
    ap.add_argument("--lote", type=int, default=2)
    ap.add_argument("--recortes", type=int, default=4, help="Recortes aleatorios por caso y época.")
    ap.add_argument("--validar-cada", type=int, default=5)
    ap.add_argument("--semilla", type=int, default=SEMILLA)
    ap.add_argument("--prueba-rapida", action="store_true",
                    help="1 época en CPU con 2 casos, espaciado 1 mm y ventana de 32 (solo comprueba que todo arranca).")
    args = ap.parse_args()

    fijar_semillas(args.semilla)
    base_cfg = PreparationConfig.from_json(args.base / "preparacion.json")
    args.version_base = base_cfg.version
    cfg = dataclasses.replace(base_cfg, nombre=args.nombre, version=args.version, pesos="models/model.pt")
    if args.prueba_rapida:
        args.max_epocas, args.dispositivo, args.recortes, args.validar_cada = 1, "cpu", 2, 1
        cfg = dataclasses.replace(cfg, espaciado=(1.0, 1.0, 1.0), roi_size=(32, 32, 32), sw_batch_size=2, overlap=0.25)
    dispositivo = elegir_dispositivo(args.dispositivo)

    # división: se crea si no existe y SIEMPRE se verifica antes de entrenar (RC-04)
    if not args.division.exists():
        crear_division(args.datos, args.division)
    division = cargar_division(args.division)
    conj = division["conjuntos"]
    ids_entr, ids_val = conj["entrenamiento"], conj["validacion"]
    if args.prueba_rapida:
        ids_entr, ids_val = ids_entr[:2], ids_val[:1]
    print(f"Dispositivo: {dispositivo} | entrenamiento={len(ids_entr)} validación={len(ids_val)} "
          f"| el conjunto de prueba ({len(conj['prueba'])} casos) no se toca aquí.")

    t0 = time.perf_counter()
    entr = [preparar_caso(args.datos, c, cfg) for c in ids_entr]
    val = [preparar_caso(args.datos, c, cfg) for c in ids_val]
    print(f"Datos preparados en {time.perf_counter() - t0:.0f} s.")

    pesos_base = None if args.desde_cero else args.base / base_cfg.pesos
    red = crear_red(cfg, pesos_base, dispositivo)
    perdida = DiceCELoss(to_onehot_y=True, softmax=True)
    optimizador = torch.optim.AdamW(red.parameters(), lr=args.lr, weight_decay=1e-5)
    usar_amp = dispositivo.type == "cuda"
    escalador = torch.amp.GradScaler(enabled=usar_amp)
    transf = transformaciones_entrenamiento(cfg, args.recortes)

    historial: list[dict] = []
    mejor = {"dice": -1.0, "epoca": 0}
    mejores_pesos = {k: v.detach().cpu().clone() for k, v in red.state_dict().items()}
    t_ini = time.perf_counter()
    for epoca in range(1, args.max_epocas + 1):
        red.train()
        recortes = [r for c in random.sample(entr, len(entr)) for r in transf(c)]
        random.shuffle(recortes)
        acumulada, n = 0.0, 0
        for i in range(0, len(recortes), args.lote):
            lote = recortes[i : i + args.lote]
            if len(lote) < 2:  # BatchNorm necesita al menos 2 muestras
                continue
            x = torch.stack([r["image"] for r in lote]).to(dispositivo)
            y = torch.stack([r["label"] for r in lote]).to(dispositivo)
            optimizador.zero_grad(set_to_none=True)
            with torch.autocast(device_type=dispositivo.type, enabled=usar_amp):
                valor = perdida(red(x), y)
            escalador.scale(valor).backward()
            escalador.step(optimizador)
            escalador.update()
            acumulada += float(valor)
            n += 1
        registro = {"epoca": epoca, "perdida": acumulada / max(n, 1)}
        if epoca % args.validar_cada == 0 or epoca == args.max_epocas:
            registro["dice_validacion"] = validar(red, val, cfg, dispositivo)
            if registro["dice_validacion"] > mejor["dice"]:
                mejor = {"dice": registro["dice_validacion"], "epoca": epoca}
                mejores_pesos = {k: v.detach().cpu().clone() for k, v in red.state_dict().items()}
        historial.append(registro)
        print(registro, flush=True)

    red.load_state_dict(mejores_pesos)  # se guarda la mejor época según la validación
    carpeta = args.salida / args.nombre
    escribir_salida(carpeta, red, cfg, args, division, historial, mejor, dispositivo, time.perf_counter() - t_ini)
    print(f"Modelo guardado en {carpeta} (mejor Dice de validación {mejor['dice']:.4f}, época {mejor['epoca']}).")


if __name__ == "__main__":
    main()
