# Especificación técnica de implementación — Prosta-AI

Documento de referencia para el código. Deriva de `docs/ejecucion/` (requisitos, arquitectura, módulos y modelo de datos). Si algo no está aquí, manda `docs/ejecucion/`; si dos fuentes chocan, ver `docs/ejecucion/05_inconsistencias.md`.

## 1. Principios
- Aplicación académica y experimental. **No diagnostica.** Ningún texto usa lenguaje clínico (RF-15, RF-16, RN-02).
- Cero datos personales en base de datos y almacenamiento (RB-01, RB-02). Solo alias + hash de contraseña.
- Monolito modular de un solo proceso: API FastAPI + tarea local (hilo) + módulo de IA. La API **nunca** llama al pipeline: crea un trabajo `pendiente` y la tarea local lo toma (RC-02).
- Stack fijo: React, FastAPI, PostgreSQL, PyTorch/MONAI (RC-01). Python 3.12.
- Nombres de clases de los patrones en inglés (como en el informe de patrones); comentarios, mensajes y textos de interfaz en español.
- Sin registro de cuentas, roles ni permisos (RC-05, DEC-01).

## 2. Estructura del repositorio
```
backend/
  pyproject.toml            dependencias con versión exacta (RA-01)
  alembic.ini, migrations/  migraciones versionadas
  prosta_ai/
    config.py               Settings (pydantic-settings, prefijo PROSTA_)
    db.py                   engine, SessionLocal, Base
    models.py               tablas SQLAlchemy (sección 4)
    security.py             bcrypt + token firmado (JWT HS256)
    storage.py              almacenamiento privado de archivos
    repositories/           UserRepository, StudyRepository, JobRepository, ResultRepository, ModelRepository
    jobs/state.py           patrón State del trabajo
    processing/service.py   ProcessingService (Facade) + DatabaseRecorder (Observer)
    processing/worker.py    ProcessingWorker (hilo que toma trabajos de uno en uno)
    api/                    app.py y routers (sección 5)
    assistant/              orientación opcional basada en una base de conocimiento fija (CU06)
    pipeline/               módulos 3, 4 y 5 (sección 3), sin dependencia de la base de datos
  tests/
frontend/                   React + Vite
entrenamiento/              scripts para Colab: división por paciente, entrenamiento, evaluación
scripts/                    arranque, descarga de pesos y datos de ejemplo
```

## 3. Pipeline (`prosta_ai/pipeline`) — contrato
El pipeline no conoce la base de datos ni FastAPI. Trabaja con rutas y devuelve datos.

```python
# pipeline/errors.py
class AdmissionError(Exception):          # rechazo en la carga (formato, tamaño)
    def __init__(self, message: str): ...
class StageError(Exception):              # fallo controlado de una etapa
    def __init__(self, stage: str, message: str): ...   # .stage, .message (español, para el usuario)

# pipeline/stages.py
STAGES = ["control de calidad", "preparación", "segmentación", "ROI", "evaluación"]

# pipeline/validators.py  (Chain of Responsibility)
class Validator:  set_next(v) -> Validator ; handle(ctx) ; check(ctx) (abstracto)
class FormatValidator, SizeValidator        # admisión (los usa la API)
class IntegrityValidator, MetadataValidator # validación detallada (los usa la tarea)
def validate_upload(files: list[UploadedFileInfo], max_bytes: int) -> str   # devuelve "DICOM" | "NIfTI"; lanza AdmissionError
@dataclass UploadedFileInfo: filename: str; size_bytes: int; head: bytes  # primeros 512 bytes

# pipeline/io.py  (Adapter)
@dataclass Volume: data: np.ndarray (3D float32); affine: np.ndarray (4x4); spacing: tuple[float,float,float]
def load_volume(files: list[Path], fmt: str) -> Volume   # DICOM: serie con SimpleITK; NIfTI: nibabel. Lanza StageError("control de calidad", ...)
def deidentify_dicom(files: list[Path]) -> None          # borra en sitio los tags que identifican personas; si no puede, lanza StageError
def save_nifti(data, affine, path) -> None               # sin metadatos de persona

# pipeline/progress.py  (Observer)
class PipelineObserver(Protocol):
    def on_stage_start(self, stage: str) -> None
    def on_stage_end(self, stage: str, duration_s: float) -> None
    def on_stage_failed(self, stage: str, message: str) -> None
class PipelineProgress: attach(obs); notify_start/notify_end/notify_failed
class TimingRecorder(PipelineObserver): durations: dict[str, float]

# pipeline/segmentation.py  (Strategy + Factory Method)
class SegmentationStrategy(ABC):
    name: str; version: str; weights_path: Path | None
    def segment(self, prepared: PreparedVolume) -> np.ndarray   # máscara binaria uint8 en el espacio preparado
class PretrainedUNetStrategy(SegmentationStrategy)   # pesos MONAI (bundle prostate_mri_anatomy u otro UNet entrenado en Colab)
class NnUNetStrategy(SegmentationStrategy)           # reservado; lanza StageError claro si no hay nnU-Net instalado
def create_strategy(name: str, weights_dir: Path) -> SegmentationStrategy

# pipeline/preparation.py  — las MISMAS transformaciones en entrenamiento e inferencia (RF-09)
def build_transforms(config: PreparationConfig)  # config leída de un JSON versionado junto a los pesos
@dataclass PreparedVolume: tensor; meta para invertir la preparación

# pipeline/roi.py
def mask_to_original_space(mask, prepared, original: Volume) -> np.ndarray  # alineada con la imagen original (RF-12)

# pipeline/evaluation.py
def dice(pred, ref) -> float ; def iou(pred, ref) -> float   # máscaras binarias; ambos vacíos -> 1.0

# pipeline/base.py  (Template Method)
@dataclass PipelineInput: files: list[Path]; fmt: str; reference_files: list[Path]; output_dir: Path
@dataclass PipelineOutput: image_path: Path; mask_path: Path; dice: float|None; iou: float|None; durations: dict[str,float]
class BasePipeline(ABC):
    def run(self, inp: PipelineInput, progress: PipelineProgress) -> PipelineOutput:
        # orden fijo: quality_control -> prepare -> segment -> build_roi -> evaluate
        # cada etapa notifica inicio/fin; si una lanza StageError, notifica fallo y relanza
class Segmentation3DPipeline(BasePipeline): __init__(self, strategy: SegmentationStrategy)
```
Salidas en `output_dir`: `imagen.nii.gz` (volumen original desidentificado, para el visor) y `mascara.nii.gz` (misma geometría que la imagen). La etapa «evaluación» corre siempre: sin referencia deja `dice=iou=None`.

Control de calidad (RF-10): volumen 3D, al menos 8 cortes y 32×32 vóxeles por corte, intensidad no constante, sin NaN, espaciado positivo; la referencia (si existe) debe tener la misma forma que la imagen. Si falla: `StageError("control de calidad", motivo)` (el motivo queda registrado en `trabajo.mensaje_error`).

## 4. Modelo de datos (PostgreSQL)
Tablas, columnas y tipos exactos de `docs/ejecucion/04_modelo_datos.md`: `usuario`, `estudio`, `archivo`, `modelo`, `trabajo`, `etapa_trabajo`, `resultado`. Valores de listas con CHECK:
- `estudio.formato` ∈ {`DICOM`, `NIfTI`}; `estudio.estado_admision` ∈ {`admitido`, `no compatible`}
- `trabajo.estado` y `etapa_trabajo.estado` ∈ {`pendiente`, `en proceso`, `completado`, `fallido`}
- `etapa_trabajo.nombre` ∈ STAGES
- `dice`, `iou` entre 0 y 1 o nulos.
Borrado en cascada desde `estudio`. Índices en `trabajo.estado` y `estudio.id_usuario`. `codigo_anonimo` con formato `EST-0001`.
La referencia opcional se distingue por ruta: `estudios/<codigo>/referencia/...`; la imagen en `estudios/<codigo>/imagen/...`; los resultados en `resultados/<id_trabajo>/`.
Estado mostrado en Mis estudios (derivado, no se guarda): `no compatible` si la admisión falló; si no, el del último trabajo (`pendiente`, `en proceso`, `completado`, `fallido`) o `listo para procesar` si no tiene trabajos.

Patrón State (`jobs/state.py`): `Job`, `JobState`, `PendingState`, `InProgressState`, `CompletedState`, `FailedState`. Transiciones válidas: pendiente→en proceso; en proceso→completado|fallido. Cualquier otra lanza `InvalidTransition`. Reintento = nuevo trabajo pendiente para el mismo estudio.

## 5. API HTTP (prefijo `/api`, JSON, token `Authorization: Bearer`)
| Método y ruta | Entrada | Salida | Notas |
|---|---|---|---|
| POST `/acceso/verificar` | `{alias}` | `{existe: bool}` | alias 3–30 caracteres `[A-Za-z0-9_.-]` |
| POST `/acceso` | `{alias, contrasena, confirmacion?}` | `{token, alias, primer_acceso: bool}` | si el alias no existe se exige `confirmacion == contrasena` (mín. 8 caracteres) y se guarda alias + hash (DEC-01). 401 si la contraseña no coincide |
| GET `/estudios` | — | lista `[{id, codigo, formato, fecha_carga, estado, id_ultimo_trabajo, dice, iou}]` | solo los del usuario |
| POST `/estudios` | multipart: `archivos` (1..n) y `referencia` (0..n, opcional) | 201 `{id, codigo, formato, estado}` | NIfTI: un `.nii`/`.nii.gz`. DICOM: varios `.dcm` o un `.zip` con la serie. Límite `PROSTA_MAX_UPLOAD_MB` (500). Rechazo: 422 `{detail: mensaje}`; se registra el estudio como `no compatible` sin guardar archivos |
| GET `/estudios/{id}` | — | estudio + lista de trabajos | 404 si no es del usuario |
| DELETE `/estudios/{id}` | — | 204 | borra filas y archivos; 409 si el estudio tiene un trabajo en proceso |
| POST `/estudios/{id}/procesar` | — | 201 trabajo | botón «Procesar» (DEC-02). 409 si no compatible o con trabajo pendiente/en proceso |
| GET `/trabajos/{id}` | — | `{id, id_estudio, codigo, estado, etapa_fallida, mensaje_error, fecha_creacion, fecha_inicio, fecha_fin, etapas: [{nombre, estado, duracion_s}]}` | el frontend lo consulta cada 1,5 s (RF-07) |
| GET `/trabajos/{id}/resultado` | — | `{id_trabajo, codigo, dice, iou, tiempo_total_s, modelo: {nombre, version}, cortes: n, forma: [x,y,z], aviso}` | 404 si no completado |
| GET `/trabajos/{id}/corte/{indice}?capa=imagen\|mascara` | — | PNG | plano axial; `mascara` es PNG RGBA transparente con la ROI en color; 404 si el trabajo no tiene máscara |
| GET `/trabajos/{id}/exportar` | — | PNG del corte central con ROI y el aviso experimental impreso (RF-15, Decorator) | |
| POST `/asistente` | `{pregunta}` (1 a 500 caracteres) | `{tema, respuesta, intro, pasos: [str], nota: str\|null, enlace: {ruta, texto}\|null, sugerencias: [str] (hasta 3), aviso}` | `tema` es el id del tema respondido, `"clinico"` si se rechaza la pregunta o `"no_entendido"` si no hay coincidencia (con 3 preguntas sugeridas). `respuesta` es la versión en texto plano (intro + pasos numerados + nota). Motor en `assistant/`: base de conocimiento curada (`conocimiento.py`, respuestas fijas y revisables), puntuación por coincidencia de palabras y frases con raíces y sinónimos (`motor.py`, solo biblioteca estándar, sin red), filtro clínico que se ejecuta primero y siempre prevalece, y contexto del usuario (`contexto.py`) para preguntas sobre sus propios estudios (estado, etapa fallida y su mensaje, Dice/IoU) con datos de la base, solo del usuario autenticado. No genera texto ni contenido clínico (RF-20–22) |
| GET `/salud` | — | `{estado: "ok"}` | sin token |

Aviso (constante única `AVISO_EXPERIMENTAL`): «Resultado experimental con fines académicos. No es un diagnóstico ni sustituye la valoración de un profesional de la salud.»

Errores: `{detail: "mensaje en español"}`. Token con vigencia de 8 h (`PROSTA_TOKEN_HORAS`).

## 6. Configuración (`.env`, prefijo `PROSTA_`)
`DATABASE_URL` (postgresql+psycopg://prosta@localhost:5433/prosta_ai, clúster local de `scripts/postgres_local.sh`), `STORAGE_DIR` (../almacenamiento), `SECRET_KEY`, `TOKEN_HORAS=8`, `MAX_UPLOAD_MB=500`, `MODELO_NOMBRE=prostate_mri_anatomy`, `MODELO_DIR` (../modelos), `WORKER_INTERVALO_S=2`, `WORKER_ACTIVO=true`, `CORS_ORIGINS=http://localhost:5173`.

## 7. Frontend (React + Vite, `frontend/`)
Pantallas (docs/ejecucion/03_modulos.md): Acceso (usuario → contraseña o primera vez), Inicio, Cargar estudios, Procesamiento (botón «Procesar», etapas con estado y tiempo, «Ver resultados»), Visualizar y comparar ROI (control deslizante de corte, vista con y sin máscara lado a lado, opacidad, Dice/IoU o «no disponible», panel explicativo RF-17, botón exportar), Mis estudios (y estado vacío), Asistente IA. Menú lateral con Cerrar sesión. Aviso experimental visible en todas las pantallas de resultados. < 768 px: menú ☰, tarjetas apiladas, tablas con scroll horizontal, visores apilados, botones a todo el ancho.

## 8. Pruebas
`pytest` en `backend/tests`: unitarias del pipeline con volúmenes sintéticos y una estrategia falsa; State; validadores; API con base SQLite temporal y `WORKER_ACTIVO=false` más ejecución manual del worker; privacidad (ningún tag identificativo tras desidentificar; ninguna columna personal). Frontend: `npm run build` sin errores.
