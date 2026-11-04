# Arquitectura de Prosta-AI

Fuentes: `fuentes/1.3.2.3_arquitectura_sistema.md`, `fuentes/1.3.2.4_arquitectura_software.md`, `fuentes/1.3.2.4b_justificacion_arquitectura_software.md`.

## Diferencia entre las dos vistas
| | Arquitectura del sistema (1.3.2.3) | Arquitectura de software (1.3.2.4) |
|---|---|---|
| Base teórica | Sommerville (2011) | Bass, Clements y Kazman (2013), citados por Pressman y Maxim (2020) |
| Nivel | Bloques grandes, nodos y servicios externos | Componentes internos del backend |
| Alternativas comparadas | Monolítica · **cliente-servidor en capas (elegida)** · microservicios | **Monolito modular de un proceso (elegido)** · backend con ejecutor separado · microservicios |

## Estilo elegido
Cliente-servidor por capas: presentación (React), aplicación (API FastAPI), procesamiento de imagen (tarea local con PyTorch/MONAI) y persistencia (PostgreSQL + almacenamiento privado). El lado servidor se despliega como **un solo proceso** con módulos separados (monolito modular).

Atributos que guiaron la decisión: rendimiento ≤ 120 s (5.1 / RR-01), protección de datos (2.2 / RB-02), mantenibilidad y reproducibilidad (3.4, 5.4 / RC-02, RA-01), restricciones del equipo (5 estudiantes, stack fijo, sin presupuesto) y disponibilidad baja aceptable (prototipo).

Razones de descarte:
- **Monolítica:** mezcla interfaz con inferencia; un cambio de modelo afecta todo.
- **Microservicios:** contenedores, orquestación y despliegues independientes; desproporcionado para el alcance.
- **Ejecutor separado:** se adopta solo si las mediciones del riesgo 1 muestran bloqueo de la API.

Restricciones del estilo (Shaw y Garlan): la API no llama directamente a la segmentación; los trabajos se procesan de uno en uno; el módulo de IA está desacoplado de la API (desacople lógico mediante módulos y la tabla de trabajos, no de proceso); acceso solo con alias y contraseña cifrada.

## Nodos físicos
| Nodo | Ejecuta | Observación |
|---|---|---|
| Equipo del usuario | Navegador con React | No guarda estudios ni resultados |
| Servidor de la aplicación | API, tarea de procesamiento, módulo de IA, PostgreSQL y almacenamiento privado | Equipo de un integrante o cualquier servidor de demostración; un solo proceso de backend |
| Google Colab | Entrenamiento y ajuste del modelo con GPU gratuita; pruebas de inferencia durante el desarrollo (riesgo 1) | Externo; no forma parte de la aplicación en uso; entrega los pesos |
| GitHub | Código, configuración versionada y documentación | Rama principal protegida, etiquetas por sprint |

Comunicaciones: navegador ↔ API por HTTP (JSON); API y tarea ↔ PostgreSQL por SQL; tarea ↔ almacenamiento por archivos; Colab → servidor: pesos del modelo; GitHub → servidor: código.

## Flujo principal (CU01–CU05)
1. **CU01:** ingreso con alias y contraseña; la API verifica en PostgreSQL. Si es la primera vez que ese alias entra, el sistema pide confirmar la contraseña y guarda el alias con su hash para reconocerlo después (identificación en el primer acceso, no registro de cuentas).
2. **CU02:** carga de un estudio DICOM o NIfTI; la API valida formato y tamaño (admisión) y guarda el archivo en el almacenamiento privado. Si se rechaza, no se crea trabajo.
3. **CU03:** el usuario pulsa «Procesar»; la API crea un **trabajo pendiente** en PostgreSQL y responde de inmediato.
4. La **tarea local** toma los trabajos pendientes uno a uno: valida integridad y privacidad (elimina metadatos o rechaza), prepara el volumen.
5. El **módulo de IA** devuelve la máscara 3D; se genera la ROI y, si hay referencia, se calculan Dice e IoU.
6. La tarea actualiza el estado del trabajo; el frontend lo **consulta** por la API y muestra la ROI con el aviso experimental (**CU04**).
7. Estudios y resultados quedan registrados para consulta (**CU05**).

Estados del trabajo: **pendiente → en proceso → completado | fallido**; un fallido puede reintentarse (vuelve a pendiente). Sin referencia, la máscara se muestra y las métricas aparecen como no disponibles.

## Vistas documentadas (justificación, IEEE 1471 y SEI «Vistas y más allá»)
- **Lógica de componentes** (prioridad 1): 7 componentes y sus responsabilidades.
- **Escenarios / casos de uso** (prioridad 1): CU01–CU06 (el «+1» de Kruchten).
- **Despliegue mínimo viable** (prioridad 2).
- **Ejecución:** integrada en la vista lógica (flujo).
- **Código:** diferida al diseño técnico (RA-01).

## Control de factibilidad
| Riesgo / condición | Acción | Decisión |
|---|---|---|
| Riesgo 1: tiempo de inferencia | Sprint 3, actividad 1408: medir CPU, GPU y memoria con un estudio representativo | Si > 120 s: Colab, modelo preentrenado más ligero o menor resolución; si persiste, documentar la limitación |
| Bloqueo de la interfaz | Comprobar que la interfaz consulta el estado mientras corre la tarea | Si se bloquea, separar el procesador |
| Privacidad e integridad | Rechazo de datos no aptos y recuperación del resultado | Ajustar validación sin ampliar alcance |

Planificación: medición temprana en Sprint 3; ROI en Sprint 4; evaluación en Sprint 5; mínimo viable integrado en Sprint 6 (actividades 1701–1706).

## Decisiones registradas
- **DEC-01:** identificación en el primer acceso (alias + contraseña confirmada, guardada como hash). No es registro de cuentas y es compatible con RC-05.
- **DEC-02:** el procesamiento inicia con el botón «Procesar»; luego es automático.
- **INC-03 (abierta):** el SRS programa casi todas las pruebas funcionales en el Sprint 6, mientras el plan de calidad exige verificar flujo y privacidad en cada integración; se propone adelantar controles a los sprints 2 y 3.
