# Prosta-AI

Aplicación web **académica y experimental** que carga estudios de resonancia magnética de próstata públicos y desidentificados (DICOM o NIfTI), los segmenta en 3D con un modelo U-Net (PyTorch/MONAI) y muestra la región de interés (ROI) superpuesta a la imagen, con las métricas Dice e IoU cuando el estudio trae máscara de referencia.

> **Prosta-AI no diagnostica.** No tiene uso clínico, no es un dispositivo médico y no trabaja con datos de pacientes reales. Los resultados son experimentales y no sustituyen la valoración de un profesional de la salud.

Proyecto del curso Gestión de Proyectos de TI, Universidad Santiago de Cali, 2026-2.

## Arquitectura

Cliente-servidor por capas, con el servidor como monolito modular de un solo proceso:

| Componente | Ubicación | Tecnología |
|---|---|---|
| 1. Presentación | `frontend/` | React + Vite |
| 2. API y servicios | `backend/prosta_ai/api/` | FastAPI |
| 3. Validación y preparación | `backend/prosta_ai/pipeline/validators.py`, `io.py`, `preparation.py` | Python, MONAI, SimpleITK, pydicom |
| 4. Segmentación y ROI | `backend/prosta_ai/pipeline/segmentation.py`, `roi.py` | PyTorch / MONAI |
| 5. Evaluación | `backend/prosta_ai/pipeline/evaluation.py` | Python |
| 6. Repositorios y archivos | `backend/prosta_ai/repositories/`, `storage.py`, `models.py` | PostgreSQL + almacenamiento privado |
| 7. Orientación opcional | `backend/prosta_ai/assistant/` | Respuestas fijas con puntuación por coincidencia, sin contenido clínico |

La API nunca llama al pipeline: al pulsar «Procesar» crea un trabajo `pendiente` en PostgreSQL y la tarea local (`processing/worker.py`) lo toma, ejecuta control de calidad → preparación → segmentación → ROI → evaluación y publica el resultado. El detalle técnico está en `docs-tecnicos/especificacion-tecnica.md`; el análisis y el diseño, en `docs/ejecucion/`.

Patrones aplicados: Facade (`ProcessingService`), Template Method (`BasePipeline`), Strategy y Factory Method (`SegmentationStrategy`, `create_strategy`), Chain of Responsibility (validadores), State (`jobs/state.py`), Observer (`PipelineProgress`, `DatabaseRecorder`, `TimingRecorder`), Decorator (aviso en la imagen exportada) y Adapter (lectores DICOM/NIfTI).

## Documentación

| Ubicación | Contenido |
|---|---|
| `docs/gestion/` | Acta de Constitución del proyecto |
| `docs/ejecucion/` | Análisis y diseño: requisitos, arquitectura, módulos, modelo de datos, inconsistencias, diagramas y pantallas (`assets/pantallas/`); los documentos completos están en `fuentes/` |
| `docs-tecnicos/especificacion-tecnica.md` | Contrato técnico del código: estructura, API, configuración y pruebas |
| `docs-tecnicos/modelo-y-licencias.md` | Modelo en uso, con qué datos y cómo fue entrenado, licencias y riesgos de derechos |
| `entrenamiento/README.md` | Entrenamiento, ajuste y evaluación del modelo en Google Colab |
| `reports/` | Estado actual del desarrollo e informes de evaluación del modelo |

## Requisitos

- Linux o macOS, Python 3.12 (se instala con [uv](https://docs.astral.sh/uv/)), Node.js 20 o superior, PostgreSQL 15 o superior (`initdb`, `pg_ctl`).
- No requiere GPU: la inferencia en CPU tarda entre 10 y 25 s por estudio.

## Instalación y arranque

```bash
scripts/instalar.sh     # entorno de Python, .env, base de datos, migraciones, pesos del modelo y frontend
scripts/arrancar.sh     # PostgreSQL local (puerto 5433), API en :8000 y frontend en :5173
```

Abra http://localhost:5173. La primera vez que entra con un alias, el sistema le pide confirmar la contraseña y desde entonces lo reconoce (no hay registro de cuentas).

Para probar con datos públicos: `backend/.venv/bin/python scripts/descargar_datos_ejemplo.py` descarga el conjunto Medical Segmentation Decathlon Task05_Prostate (CC-BY-SA 4.0) en `datos/`. Cargue `imagesTr/prostate_XX.nii.gz` como estudio y `labelsTr/prostate_XX.nii.gz` como máscara de referencia.

## Pruebas

```bash
cd backend && .venv/bin/pytest
cd frontend && npm run build
```

## Modelo y datos

- Modelo: por ahora se usa el bundle preentrenado `prostate_mri_anatomy` del MONAI Model Zoo (Apache 2.0), entrenado por sus autores con Prostate158 (T2w, 3 T). Con qué y cómo se entrenó, sus licencias y los riesgos de uso están en `docs-tecnicos/modelo-y-licencias.md`. Ficha en `modelos/prostate_mri_anatomy/FICHA.md` tras la descarga.
- Entrenamiento y evaluación propios (Google Colab): ver `entrenamiento/README.md`. La división por paciente está en `entrenamiento/division_task05.json` y los informes de evaluación en `reports/evaluacion/`.

## Privacidad

- Solo se guardan el alias y el hash bcrypt de la contraseña; ninguna tabla tiene datos personales.
- Los archivos se guardan con nombres neutros (`archivo_001.dcm`). Antes de leer un DICOM se eliminan los datos de persona, institución, fechas y etiquetas privadas; si no es posible, el estudio se rechaza y sus archivos se eliminan. Los `.zip` originales se borran después de desidentificar su contenido.
- Imágenes, máscaras y pesos se guardan fuera de la base de datos (`almacenamiento/`, `modelos/`), y git los ignora.

## Marco legal

Ley 1581 de 2012 y Decreto 1377 de 2013 (protección de datos personales), Ley 23 de 1981 (la decisión médica es del profesional) y CONPES 3975.
