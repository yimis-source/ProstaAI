# Modelo de datos de Prosta-AI

Fuente: `fuentes/1.3.2.5_arquitectura_datos.md` (Casas Roma: 5 fases; IBM: arquitectura de datos). Base de datos PostgreSQL; archivos pesados en almacenamiento privado.

## Flujo de los datos
Recopilación (carga DICOM/NIfTI) → Validación (formato, tamaño, integridad, desidentificación; si no cumple, el archivo se rechaza y no se guarda) → Transformación (preparación, segmentación 3D, ROI) → Evaluación (Dice e IoU si hay referencia) → Consumo (visor de ROI e historial). Los datos de entrenamiento se usan fuera, en Google Colab; al sistema solo llegan los pesos.

## Entidades y relaciones (modelo conceptual)
| Relación | Cardinalidad | Significado |
|---|---|---|
| Usuario — carga — Estudio | 1 : N | Un usuario carga varios estudios |
| Estudio — contiene — Archivo | 1 : N | Un estudio tiene uno o varios archivos |
| Estudio — se procesa en — Trabajo | 1 : N | Un estudio puede procesarse más de una vez (reintentos) |
| Modelo — se usa en — Trabajo | 1 : N | Cada trabajo usa una versión del modelo |
| Trabajo — registra — Etapa | 1 : N | Cada trabajo registra sus etapas |
| Trabajo — produce — Resultado | 1 : 0..1 | Solo un trabajo completado produce resultado |

## Tablas (modelo lógico y físico)
### usuario
| Columna | Tipo | Clave |
|---|---|---|
| id_usuario | INTEGER (identity) | PK |
| alias | VARCHAR(30) | UQ |
| hash_contrasena | VARCHAR(255) | |
| fecha_creacion | TIMESTAMPTZ | |

### estudio
| Columna | Tipo | Clave |
|---|---|---|
| id_estudio | INTEGER | PK |
| codigo_anonimo | VARCHAR(12) | UQ (ej. EST-0264) |
| id_usuario | INTEGER | FK → usuario |
| formato | VARCHAR(5) | lista: DICOM, NIfTI |
| fecha_carga | TIMESTAMPTZ | |
| estado_admision | VARCHAR(15) | lista: admitido, no compatible |

### archivo
| Columna | Tipo | Clave |
|---|---|---|
| id_archivo | INTEGER | PK |
| id_estudio | INTEGER | FK → estudio |
| ruta | VARCHAR(255) | |
| tamano_bytes | BIGINT | |
| hash_sha256 | CHAR(64) | |
| valido | BOOLEAN | |

### modelo
| Columna | Tipo | Clave |
|---|---|---|
| id_modelo | INTEGER | PK |
| nombre | VARCHAR(50) | UQ con version |
| version | VARCHAR(20) | UQ con nombre |
| ruta_pesos | VARCHAR(255) | |
| hash_pesos | CHAR(64) | |
| ruta_configuracion | VARCHAR(255) | |
| fecha_registro | TIMESTAMPTZ | |

### trabajo
| Columna | Tipo | Clave |
|---|---|---|
| id_trabajo | INTEGER | PK |
| id_estudio | INTEGER | FK → estudio |
| id_modelo | INTEGER | FK → modelo |
| estado | VARCHAR(12) | lista: pendiente, en proceso, completado, fallido (índice) |
| fecha_creacion / fecha_inicio / fecha_fin | TIMESTAMPTZ | |
| etapa_fallida | VARCHAR(25) | |
| mensaje_error | TEXT | |

### etapa_trabajo
| Columna | Tipo | Clave |
|---|---|---|
| id_etapa | INTEGER | PK |
| id_trabajo | INTEGER | FK → trabajo |
| nombre | VARCHAR(25) | lista: control de calidad, preparación, segmentación, ROI, evaluación |
| estado | VARCHAR(12) | |
| fecha_inicio / fecha_fin | TIMESTAMPTZ | |
| duracion_s | NUMERIC(7,2) | |

### resultado
| Columna | Tipo | Clave |
|---|---|---|
| id_resultado | INTEGER | PK |
| id_trabajo | INTEGER | FK → trabajo, UQ |
| ruta_mascara | VARCHAR(255) | |
| dice | NUMERIC(4,3) | 0–1, nulo sin referencia |
| iou | NUMERIC(4,3) | 0–1, nulo sin referencia |
| tiempo_total_s | NUMERIC(7,2) | |
| fecha_registro | TIMESTAMPTZ | |

## Reglas físicas
- Borrado en cascada de archivos, trabajos, etapas y resultados al eliminar un estudio.
- Índices en `trabajo.estado` (la tarea consulta pendientes) y `estudio.id_usuario` (historial).
- Contraseñas solo como hash con sal (por ejemplo, bcrypt).
- Imágenes, máscaras y pesos fuera de la base; solo ruta y hash; sin metadatos identificables.
- El estado mostrado en Mis estudios (completado, listo para procesar, no compatible) se deriva de `estado_admision` y del último trabajo; no se guarda dos veces.
- Implementación en Sprint 6 (actividad 1703) con migraciones versionadas; verificación de cero datos personales (actividad 1711).

## Trazabilidad datos → requisitos
4.7 (usuario), 2.2 (sin datos personales), 4.1 (estudio y archivo), 4.2 (trabajo y etapa), 4.5 (resultado), 3.5 y 5.1 (métricas y tiempos), 5.4 (modelo y versión).
