# Módulos (componentes) de Prosta-AI

Fuentes: arquitectura de software (Figura 1, Tabla 2), justificación (Tabla 12), informe de patrones y diseño de interfaz y módulos (Figura 2).

## Los 7 componentes
| # | Componente | Responsabilidad | Tecnología | Requisitos del SRS | Matriz |
|---|---|---|---|---|---|
| 1 | Presentación React | Carga, consulta del avance, visualización de cortes y ROI, historial | React | RF-07, RF-13, RF-14, RF-15, RF-17, RU-01 | 4.3, 4.4, 2.3, 5.2 |
| 2 | API y servicios de aplicación | Acceso con alias y contraseña, admisión del estudio, creación de trabajos, recuperación de resultados | FastAPI | RF-01, RF-02, RF-03, RF-04, RF-06, RF-08, RF-19, RC-05 | 4.7, 4.1, 4.2, 4.5 |
| 3 | Validación y preparación | Comprobar entrada, privacidad y geometría; acondicionar el volumen | Python + MONAI | RF-04, RF-05, RF-09, RF-10, RR-01 (preparación) | 2.2, 3.2 |
| 4 | Segmentación y ROI | Ejecutar el modelo versionado y devolver la máscara alineada | PyTorch / MONAI | RF-11, RF-12, RR-01 (inferencia) | 3.4, 4.3 |
| 5 | Evaluación | Comparar máscara y referencia; informar Dice e IoU cuando aplique | Python | RF-23, RF-24, RC-04 | 3.5 |
| 6 | Repositorios y archivos | Persistir usuarios (alias + hash), trabajos y estados en PostgreSQL; custodiar archivos privados | PostgreSQL + almacenamiento de archivos | RF-18, RB-01, RB-02, RC-03 | 4.5, 2.2 |
| 7 | Orientación opcional | Explicar el uso y sus límites sin decisiones clínicas | Agente de IA | RF-20, RF-21, RF-22 | 4.6 (Could) |

Requisitos transversales (sin componente único): RF-16, RN-01 a RN-03, RC-01, RC-02, RC-06, RA-01, RA-02.

## Dependencias entre componentes
| Origen | Destino | Qué pasa | Tipo |
|---|---|---|---|
| 1 Presentación | 2 API | Solicitudes HTTP: acceso, carga, «Procesar», consulta de estado y resultados | Llamada |
| 2 API | 6 Repositorios | Verifica usuarios, registra estudio admitido y **crea trabajo pendiente** | Escritura |
| 6 Repositorios | 3 Validación | La tarea local consulta el trabajo pendiente | Lectura (coordinación por tabla de trabajos) |
| 3 Validación | 4 Segmentación | Volumen preparado | Encadenamiento |
| 4 Segmentación | 5 Evaluación | Máscara 3D (si hay referencia) | Encadenamiento |
| 5 Evaluación | 6 Repositorios | Publica estado y resultado | Escritura |
| 2 API | 7 Orientación | Consultas de orientación (opcional) | Llamada opcional |

La API nunca llama directamente a 3, 4 o 5: la tabla de trabajos en PostgreSQL es el punto de coordinación (RC-02).

## Patrones de diseño por componente
| Patrón | Familia | Clases (nombres en inglés) | Componente | Problema que resuelve | Req. matriz |
|---|---|---|---|---|---|
| Facade | Estructural | ProcessingService (fachada), Segmentation3DPipeline, JobRepository, ProcessingWorker (cliente) | 3–6 | Una sola llamada para todo el procesamiento | 3.4, 4.2 |
| Template Method | Comportamiento | BasePipeline (método `run`), Segmentation3DPipeline | 3–5 | Orden fijo: control de calidad → preparación → segmentación → ROI → evaluación | 3.2, 4.2 |
| Strategy | Comportamiento | SegmentationStrategy, PretrainedUNetStrategy, NnUNetStrategy | 4 | Cambiar el modelo por configuración versionada | 3.4, 5.4 |
| Chain of Responsibility | Comportamiento | Validator; FormatValidator, SizeValidator (admisión en la API); IntegrityValidator, MetadataValidator (validación detallada en la tarea) | 2, 3 | Validaciones encadenadas del archivo | 2.2, 4.1 |
| State | Comportamiento | Job, JobState, PendingState, InProgressState, CompletedState, FailedState | 6 | Transiciones válidas del trabajo | 4.2, 4.5 |
| Observer | Comportamiento | PipelineProgress (sujeto), DatabaseRecorder, TimingRecorder | 3–6 | Registrar avance y tiempos sin acoplar el pipeline | 4.2, 5.1 |

Complementarios opcionales: Decorator (aviso experimental en salidas), Adapter (PyTorch/MONAI y lectores DICOM/NIfTI), Factory Method (crear la estrategia), Singleton (pesos en memoria, con cautela), Composite (árbol de componentes de React). No aplicados por sobreingeniería: Abstract Factory, Builder, Prototype, Bridge, Flyweight, Mediator, Memento, Iterator, Command, Visitor.

## Pantallas (componente 1) y navegación
Pantallas diseñadas (SVG): CU00 Inicio; CU01 Acceso (usuario), Acceso (contraseña), Acceso (primera vez, con «Verificar contraseña»); CU02 Cargar estudios; CU03 Procesamiento; CU04 Visualizar y comparar ROI; CU05 Mis estudios y Mis estudios (vacío); CU06 Asistente IA.

Transiciones principales:
- Acceso (usuario) → «Continuar» → Acceso (contraseña) si existe, o Acceso (primera vez) si es nuevo.
- Acceso (contraseña) → «Acceder» → Inicio; Acceso (primera vez) → «Acceder por primera vez» → Inicio.
- Inicio → Cargar estudios («Cargar un estudio / Cargar archivos»), Procesamiento («Ir a procesamiento / Procesar»), Mis estudios («Ver todos los estudios»), Visualizar ROI («Abrir comparador / Ver ROI»), Asistente IA («Abrir asistente»).
- Cargar estudios → «Continuar a procesamiento» → Procesamiento; en Procesamiento el botón «Procesar» inicia el procesamiento (en las pantallas de la versión entregada aparece como «Ejecutar», ver I-02); «Ver resultados» → Visualizar ROI.
- Visualizar ROI ↔ Mis estudios («Mis estudios» / «Ver ROI»); Mis estudios → «Cargar un estudio», «Procesar / Ver detalles».
- Menú lateral en todo el espacio de trabajo: Inicio, Cargar estudios, Procesamiento, Visualizar ROI, Mis estudios, Asistente IA, Cerrar sesión.

Pantallas pequeñas (< 768 px): menú en botón ☰, tarjetas apiladas, tablas con desplazamiento horizontal, visores apilados, botones a todo el ancho; el aviso experimental se mantiene visible.
