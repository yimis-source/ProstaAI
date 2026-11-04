# Requisitos de Prosta-AI

Fuente principal: SRS v1.0 (`fuentes/1.3.1.1_SRS_requisitos_ISO29148.md`), estructurado según ISO/IEC/IEEE 29148:2018. Cada requisito tiene ID único, prioridad MoSCoW y origen en la matriz de trazabilidad (`fuentes/1.3.1.2_matriz_trazabilidad.md`). Redacción: «deberá» = Must, «debería» = Should, «podrá» = Could.

Métodos de verificación: **P** prueba, **I** inspección, **D** demostración, **A** análisis. El sprint indica cuándo se verifica.

## Requisitos funcionales (RF)

| ID | Requisito | Prioridad | Origen (matriz) | CU | Verificación |
|---|---|---|---|---|---|
| RF-01 | Ingreso a la aplicación mediante un inicio de sesión básico | Should | 4.7 | CU01 | P · S6 |
| RF-02 | Cargar uno o varios estudios de MRI de prueba desde la aplicación web | Must | 4.1 | CU02 | P · S6 |
| RF-03 | Validar formato y tamaño de cada archivo; aceptar solo los formatos definidos y rechazar los demás con mensaje claro | Must | 4.1 | CU02 | P · S6 |
| RF-04 | Detectar archivos corruptos o no válidos y rechazarlos con mensaje claro | Must | 4.1 | CU02 | P · S6 |
| RF-05 | Eliminar los metadatos que identifiquen a una persona o, si no es posible, rechazar el archivo | Must | 2.2 | CU02 | P · S6 |
| RF-06 | Ejecutar automáticamente control de calidad, preparación, segmentación 3D y generación de la ROI | Must | 4.2 | CU03 | P · S6 |
| RF-07 | Informar al usuario el estado de cada etapa del procesamiento | Must | 4.2 | CU03 | P · S6 |
| RF-08 | Mostrar mensaje claro y detener el flujo de forma controlada si falla una etapa | Must | 4.2 | CU03 | P · S6 |
| RF-09 | Aplicar en la inferencia las mismas transformaciones de preparación usadas en el entrenamiento | Must | 3.2 | CU03 | P · S2 |
| RF-10 | Excluir y registrar, con su motivo, toda imagen que no supere el control de calidad | Must | 3.2 | CU03 | P · S2 |
| RF-11 | Delimitar la próstata con un modelo de segmentación 3D (U-Net o nnU-Net) y entregar la máscara | Must | 3.4 | CU03 | P · S3 |
| RF-12 | Generar la ROI a partir de la segmentación, alineada con la imagen original | Must | 4.3 | CU03 | I · S4 |
| RF-13 | Mostrar la ROI superpuesta y alineada sobre la imagen original | Must | 4.3 | CU04 | P · S4, S6 |
| RF-14 | Comparar la imagen original con y sin la máscara | Must | 4.3 | CU04 | P · S4, S6 |
| RF-15 | Mostrar en toda pantalla de resultados y salida exportada el aviso de resultado experimental, académico y no diagnóstico | Must | 2.3 | CU04 | I · S4, S6 |
| RF-16 | No usar lenguaje clínico ni sugerir diagnóstico, certificación o aprobación médica | Must | 2.3 | CU04 | I · S4, S6 |
| RF-17 | Panel que explique qué muestra la ROI, qué significan las métricas y sus limitaciones | Must | 4.4 | CU04 | I · S4, S6 |
| RF-18 | Registrar cada estudio procesado, con resultado y métricas, en la base de datos y el almacenamiento | Should | 4.5 | CU05 | P · S6 |
| RF-19 | Consultar los estudios y resultados registrados | Should | 4.5 | CU05 | P · S6 |
| RF-20 | Asistente de IA que oriente sobre el uso de la aplicación | Could | 4.6 | CU06 | D · S6 |
| RF-21 | Cada agente con funciones definidas en el diseño y salidas revisables | Could | 4.6 | CU06 | I · S6 |
| RF-22 | Los agentes no toman decisiones autónomas ni generan contenido clínico | Could | 4.6 | CU06 | P · S6 |
| RF-23 | Calcular Dice e IoU por caso y en promedio sobre el conjunto de prueba, con condiciones y limitaciones | Must | 3.5 | — | A · S5 |
| RF-24 | Dice medio ≥ 0,80 en el conjunto de prueba; si no se alcanza, documentar brecha y causas | Should | 3.5 | — | A · S5 |

## Requisitos no funcionales

| ID | Tipo | Requisito | Prioridad | Origen | Verificación |
|---|---|---|---|---|---|
| RU-01 | Usabilidad | Usuarios de prueba completan carga, procesamiento y visualización sin asistencia; los hallazgos se registran y corrigen | Should | 5.2; CU01–CU05 | P · S6 |
| RR-01 | Rendimiento | Procesar un estudio en ≤ 2 min (120 s), desde que inicia el procesamiento hasta que se muestra el resultado | Should | 5.1; CU03 | P · S5, S6 |
| RB-01 | Base de datos | Modelo de datos con estudios, resultados y métricas, sin campos de identificación personal | Must | 4.5, 2.2; CU05 | I · S6 |
| RB-02 | Base de datos | Ni la base de datos ni el almacenamiento contienen datos personales identificables | Must | 2.2 | I · cada integración |
| RC-01 | Restricción | Stack React, FastAPI, PostgreSQL, PyTorch/MONAI y Git/GitHub; cambios de tecnología por control de cambios | Must | 5.3 | I · S2 |
| RC-02 | Restricción | Arquitectura cliente-servidor con el módulo de IA desacoplado del servicio de aplicación | Must | 5.3, 3.4 | I · S2 |
| RC-03 | Restricción | Solo conjuntos públicos y anónimos, cada uno con ficha de fuente, licencia, condiciones y cita | Must | 2.1, 3.1 | I · S1 |
| RC-04 | Restricción | División por paciente en entrenamiento, validación y prueba, sin pacientes repetidos; se verifica antes de entrenar | Must | 3.3 | P · S2 |
| RC-05 | Restricción | No implementar registro de cuentas, roles ni permisos adicionales al acceso básico (la identificación en el primer acceso no es un registro de cuentas; ver DEC-01) | Must | 4.7 | I · S6 |
| RC-06 | Restricción | Solo aplicación web, sin app móvil ni alta disponibilidad | Must | Acta 3.1.2 | I · S6 |
| RN-01 | Norma | Cumplir Ley 1581 de 2012 y Decreto 1377 de 2013 | Must | 2.1, 2.2 | I · S1, S6 |
| RN-02 | Norma | No presentarse como software ni dispositivo médico (Ley 23 de 1981) | Must | 2.3 | I · S6 |
| RN-03 | Norma | Requisitos redactados e identificados según ISO/IEC/IEEE 29148 | Must | 6.1 | I · S2 |
| RA-01 | Atributo (reproducibilidad) | Repositorio con instrucciones, versiones exactas, configuración, semillas y pesos | Should | 5.4 | D · S7 |
| RA-02 | Atributo (trazabilidad) | Cada requisito vinculado en la matriz a necesidad, entregable, prueba e interesado | Must | 6.1, 6.4 | I · cada sprint |

## Requisitos que quedan fuera del SRS
Los requisitos de gestión del proyecto (matriz 1.1–1.4 y 6.2–6.5) se documentan en el Plan para la Dirección del Proyecto. La matriz además tiene los requisitos de datos 2.1, 3.1 y 3.3, que en el SRS aparecen como restricciones (RC-03, RC-04).

## Decisiones vigentes que precisan el SRS
- **DEC-01 (identificación en el primer acceso):** no existe registro de cuentas (RC-05). El acceso es con alias y contraseña; la primera vez que alguien entra, el sistema le pide confirmar la contraseña para poder reconocerlo en los siguientes accesos y guarda solo el alias y el hash. Sin formulario de registro, roles, permisos ni datos personales.
- **DEC-02 (inicio del procesamiento):** el usuario carga (CU02) y luego pulsa «Procesar» (CU03); desde ahí todo el flujo corre solo.
- **Formatos admitidos:** DICOM y NIfTI.
- **Google Colab:** servicio externo para entrenar el modelo y para pruebas de inferencia durante el desarrollo; la aplicación en uso infiere en su servidor.

## Exclusiones (Won't, Acta 3.1.2)
Uso clínico o diagnóstico; validación con radiólogos o ensayos clínicos; datos de pacientes reales o recolección de estudios; registro ante el INVIMA o certificación como dispositivo médico; agentes de IA autónomos o no revisables; producción con alta disponibilidad, soporte y mantenimiento; aplicación móvil; roles, permisos y administración de usuarios.

## Trazabilidad necesidad → requisitos (SRS, Tabla 19)
| Necesidad (Acta 3.3) | Requisitos |
|---|---|
| N1 Aplicar y evaluar el ciclo de gestión de proyectos de TI | RN-03, RA-02 |
| N2 Segmentación 3D automática en un flujo fácil de usar | RF-01, RF-02, RF-03, RF-06, RF-07, RF-08, RF-11, RU-01, RR-01 |
| N3 Ver la ROI superpuesta | RF-12, RF-13, RF-14 |
| N4 Entender límites sin confundir con diagnóstico | RF-15, RF-16, RF-17, RN-02 |
| N5 Desempeño medido con métricas trazables | RF-18, RF-19, RF-23, RF-24, RB-01, RC-04 |
| N6 No tratar información personal y respetar leyes y licencias | RF-05, RB-02, RC-03, RN-01 |
| N7 Coherencia entre requisitos, diseño, código, pruebas y entregables | RC-01, RC-02, RA-01, RA-02, RN-03 |
| N8 Automatización y agentes de IA (opcional) | RF-20, RF-21, RF-22 |
