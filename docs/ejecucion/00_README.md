# Base de conocimiento — Prosta-AI (documentos de ejecución)

Base de conocimiento en Markdown de los entregables de **Ejecución** (fase de análisis y fase de diseño) del proyecto **Prosta-AI**, curso Gestión de Proyectos de TI, Universidad Santiago de Cali, periodo 2026-2. Permite consultar el proyecto sin abrir los PDF originales.

## Resumen del proyecto
- **Qué es:** aplicación web académica y experimental que carga estudios de resonancia magnética (MRI) de próstata públicos y desidentificados (DICOM o NIfTI), los segmenta en 3D con IA (U-Net / nnU-Net en PyTorch/MONAI) y muestra la región de interés (ROI) superpuesta a la imagen, con métricas Dice e IoU cuando hay máscara de referencia.
- **Qué NO es:** no diagnostica, no tiene uso clínico, no es dispositivo médico, no usa datos de pacientes reales.
- **Marco legal:** Ley 1581 de 2012 y Decreto 1377 de 2013 (datos personales); Ley 23 de 1981 (la decisión médica es del profesional); CONPES 3975 (política de IA).
- **Gestión y desarrollo:** PMBOK 6 + plantillas Open PM/PM²; desarrollo con TSP en 7 sprints; requisitos según ISO/IEC/IEEE 29148.
- **Stack:** React (frontend), FastAPI (API), PostgreSQL (datos), PyTorch/MONAI (IA), Git/GitHub; Google Colab gratuito para entrenar. Sin presupuesto.
- **Calendario:** 28/09/2026 – 09/12/2026. Hitos H001 (05/10) a H009 (09/12). Sprint 2 (26–30/10) = diseño; Sprint 3 = modelo; Sprint 4 = ROI; Sprint 5 = evaluación; Sprint 6 (26/11–02/12) = integración web; Sprint 7 = cierre.
- **Actor único:** usuario académico (estudiante o docente). Casos de uso CU01–CU06.

## Equipo y roles
| Integrante | Rol PM² | Rol de gestión | Rol de desarrollo |
|---|---|---|---|
| Jair Enrique Sanclemente Castro | Propietario del Proyecto (product owner, docente) | — | — |
| Yimis Buenaventura | Director de Proyecto | Trazabilidad | Líder |
| Juan David Riascos Erazo | Equipo central | Monitoreo y control | Analista |
| Sergio Gabriel Meneses Silva | Equipo central | Cierre | Diseñador |
| Yeison Bolaños Ruiz | Equipo central | Inicio | Desarrollador |
| Fernando José Angulo Núñez | Equipo central | Planeación | Tester |

## Mapa de archivos
| Archivo | Contenido |
|---|---|
| `01_requisitos.md` | Los 39 requisitos del SRS (funcionales y no funcionales), con prioridad MoSCoW, origen en la matriz, caso de uso y verificación |
| `02_arquitectura.md` | Arquitectura del sistema y de software: estilo, capas, alternativas, flujo, despliegue y decisiones |
| `03_modulos.md` | Los 7 componentes: responsabilidades, dependencias, requisitos, patrones y pantallas |
| `04_modelo_datos.md` | Modelo de datos: entidades, tablas, columnas, claves, relaciones y restricciones |
| `05_inconsistencias.md` | Contradicciones y vacíos detectados entre documentos, con su corrección sugerida |
| `fuentes/` | Conversión completa de cada documento original a Markdown (texto aplanado) |
| `assets/diagrama_casos_de_uso.png` | Diagrama UML de casos de uso CU01–CU06 |

## Documentos fuente (paquetes de la EDT)
| Paquete EDT | Documento | Archivo en `fuentes/` |
|---|---|---|
| 1.3.1.1 | SRS — Requisitos funcionales y no funcionales (ISO 29148) | `1.3.1.1_SRS_requisitos_ISO29148.md` |
| 1.3.1.1 | Diagrama de casos de uso | `assets/diagrama_casos_de_uso.png` |
| 1.3.1.2 | Matriz de trazabilidad de requisitos (v1.0, con columna de caso de uso) | `1.3.1.2_matriz_trazabilidad.md` |
| 1.3.2.1 | Diseño de interfaz y módulos del sistema | `1.3.2.1_diseno_interfaz_y_modulos.md` |
| 1.3.2.2 | Informe de patrones de diseño aplicados | `1.3.2.2_informe_patrones_diseno.md` |
| 1.3.2.3 | Arquitectura del sistema | `1.3.2.3_arquitectura_sistema.md` |
| 1.3.2.4 | Arquitectura de software | `1.3.2.4_arquitectura_software.md` |
| 1.3.2.4 | Justificación (documentación) de la arquitectura de software | `1.3.2.4b_justificacion_arquitectura_software.md` |
| 1.3.2.5 | Arquitectura de datos (base de datos) | `1.3.2.5_arquitectura_datos.md` |

## Dos numeraciones de requisitos
- **Matriz de trazabilidad:** 1.1–1.4 (gestión), 2.1–2.3 (legal), 3.1–3.5 (datos y modelo), 4.1–4.7 (funcionales), 5.1–5.4 (no funcionales), 6.1–6.5 (diseño, calidad y documentación). La usan arquitectura de sistema, de software, de datos y el informe de patrones.
- **SRS:** RF (funcionales), RU (usabilidad), RR (rendimiento), RB (base de datos), RC (restricciones de diseño), RN (normas), RA (atributos). La usa la justificación de la arquitectura. La equivalencia está en la columna «Origen» del SRS y en `01_requisitos.md`.

## Glosario mínimo
- **ROI:** región de interés; aquí, la próstata delimitada por el modelo.
- **Dice:** 2|P∩G| / (|P|+|G|), de 0 a 1; meta ≥ 0,80. **IoU:** |P∩G| / |P∪G|, se reporta junto al Dice.
- **Trabajo:** solicitud de procesamiento creada al pulsar «Procesar»; estados pendiente, en proceso, completado, fallido.
- **Estudio:** conjunto de imágenes MRI de un paciente anónimo (código tipo EST-0264).
- **MoSCoW:** Must (deberá), Should (debería), Could (podrá), Won't (no se implementa).

## Regla para resolver contradicciones
Si dos documentos se contradicen, revisar `05_inconsistencias.md`. Las decisiones más recientes del equipo prevalecen sobre el texto del SRS v1.0: (1) no hay registro de cuentas; el sistema solo identifica a quien entra por primera vez con un alias y una contraseña confirmada; (2) formatos DICOM y NIfTI; (3) el procesamiento se inicia con el botón «Procesar»; (4) Google Colab es un servicio externo para entrenar el modelo y para pruebas de inferencia durante el desarrollo; la aplicación en uso infiere en su propio servidor.
