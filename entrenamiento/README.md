# Entrenamiento y evaluación de Prosta-AI

Aplicación académica y experimental, **no diagnóstica**. Esta carpeta contiene lo necesario para
reproducir la división de datos, el ajuste fino de la UNet 3D y la evaluación (RA-01).

> **Estado:** la aplicación usa por ahora el modelo preentrenado `prostate_mri_anatomy` sin ajuste (decisión del
> 04/11/2026; ver `docs-tecnicos/modelo-y-licencias.md`). El ajuste fino de esta carpeta es una mejora posterior:
> solo se adopta si supera el Dice del preentrenado (0,8925) en el mismo conjunto de prueba.

| Archivo | Función |
|---|---|
| `division.py` | División por paciente 70/15/15 (semilla 2026) y verificación de que no hay pacientes repetidos (RC-04). Escribe `division_task05.json`. |
| `entrenar.py` | Ajuste fino (o entrenamiento desde cero) con MONAI. Usa la preparación de `prosta_ai.pipeline.preparation` (RF-09). |
| `evaluar.py` | Dice e IoU por caso y promedio sobre el conjunto de prueba con `build_pipeline`; escribe `reports/evaluacion/`. |
| `Prosta_AI_entrenamiento.ipynb` | Cuaderno de Google Colab con todo el flujo. |

## Requisitos

Python 3.12 con las versiones de `backend/pyproject.toml` (numpy 1.26.4, nibabel 5.3.2, SimpleITK 2.4.0,
monai 1.4.0, torch 2.5.1, entre otras). Los comandos se ejecutan desde la **raíz del repositorio**:

```bash
cd backend && uv sync && cd ..        # o el entorno que use el equipo (backend/.venv)
backend/.venv/bin/python scripts/descargar_modelo.py          # bundle prostate_mri_anatomy
backend/.venv/bin/python scripts/descargar_datos_ejemplo.py   # MSD Task05_Prostate (CC-BY-SA 4.0)
```

## Pasos

1. **División** (se crea sola si no existe; se verifica siempre antes de entrenar):
   `backend/.venv/bin/python -m entrenamiento.division`
2. **Comprobación rápida en CPU** (1 época, 2 casos, espaciado 1 mm, ventana 32; no es un modelo útil):
   `backend/.venv/bin/python -m entrenamiento.entrenar --prueba-rapida --salida /tmp/prueba`
3. **Entrenamiento real** (recomendado en GPU, ver el cuaderno):
   `backend/.venv/bin/python -m entrenamiento.entrenar --max-epocas 100 --dispositivo cuda`
   Opciones útiles: `--desde-cero`, `--lr`, `--recortes`, `--validar-cada`, `--nombre`, `--version`, `--semilla`.
4. **Evaluación** sobre el conjunto de prueba:
   `backend/.venv/bin/python -m entrenamiento.evaluar --modelo prostate_mri_anatomy`
   (`--todos` añade los 32 casos como dato adicional; `--dispositivo cpu|cuda`).

## Qué se guarda

`modelos/<nombre>/` contiene `models/model.pt` (pesos), `preparacion.json` (idéntico formato al que lee
`create_strategy`), `metadatos.json` (versión, fecha, hash SHA-256 de los pesos, hiperparámetros, semilla y
huella de la división), `division.json`, `historial.json` y `FICHA.md`. Se guarda la época con mejor Dice de
validación. `modelos/` no se versiona en git.

Para usar un modelo propio en la aplicación, copie su carpeta a `modelos/<nombre>/` y defina
`PROSTA_MODELO_NOMBRE=<nombre>` en `backend/.env`: `create_strategy` acepta cualquier nombre cuya carpeta
contenga `preparacion.json`.

## Decisiones

- Etiquetas: Task05 usa 1 = zona periférica y 2 = zona de transición; el modelo base usa 1 = glándula central
  y 2 = periférica. Al entrenar se intercambian. La próstata completa es la unión de etiquetas > 0.
- Imagen: canal 0 (T2) del NIfTI 4D, igual que la aplicación.
- Semilla fija 2026 (Python, NumPy, torch y MONAI). En GPU puede haber pequeñas variaciones entre ejecuciones.
- El conjunto de prueba no se usa durante el entrenamiento ni para elegir la mejor época.

## Limitaciones

El Dice medio depende mucho de pocos casos (5 en prueba). Ver la sección de limitaciones de cada informe
en `reports/evaluacion/`, en particular el posible solapamiento entre los datos del modelo base y Task05.
