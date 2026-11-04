# Modelo de segmentación y licencias

## 1. Decisión vigente

Desde el 04/11/2026, Prosta-AI usa **por ahora** el modelo preentrenado `prostate_mri_anatomy` del MONAI Model Zoo, sin ajuste propio.

- **Motivo:** cumple la meta de RF-24 con margen. En el conjunto de prueba de Task05 obtiene un Dice medio de 0,8925, frente a la meta de 0,80. Funciona en CPU en 10–25 s por estudio, dentro de RR-01. Además, se ajusta a la respuesta prevista para el riesgo 1 del Acta: «modelos preentrenados con ajustes ligeros».
- **Ajuste ligero:** queda como mejora posterior. El procedimiento ya está preparado en `entrenamiento/`.
  - Si se ejecuta, el modelo ajustado solo se adopta si mejora el Dice del preentrenado en el mismo conjunto de prueba.
  - Cambiar de modelo no requiere tocar código: basta con `PROSTA_MODELO_NOMBRE` (ver `entrenamiento/README.md`).

## 2. Ficha del modelo

| Campo | Valor |
|---|---|
| Nombre | Prostate MRI Anatomy (`prostate_mri_anatomy`), versión 0.3.6 |
| Origen | MONAI Model Zoo, publicado en https://huggingface.co/MONAI/prostate_mri_anatomy (revisión fijada en `scripts/descargar_modelo.py`) |
| Autores | Lisa C. Adams y Keno K. Bressem (Charité – Universitätsmedizin Berlin) |
| Licencia del modelo | Apache License 2.0. Copyright (c) Keno Bressem |
| SHA-256 de los pesos | `3c18e4c658bb088f551b1d63219ef8340fe6256d016c75fc140d3da49dda696d` |
| Uso previsto según sus autores | «This is an example, not to be used for diagnostic purposes» |
| Versiones con que se publicó | MONAI 1.4.0, PyTorch 2.4.0 |

### Con qué datos se entrenó

- **Conjunto:** Prostate158 (https://doi.org/10.5281/zenodo.6481141). Son 158 resonancias biparamétricas de próstata adquiridas a 3 T en la Charité – Universitätsmedizin Berlin y anotadas por radiólogos expertos.
- **División de los autores:**
  - 139 estudios para entrenamiento, que son los publicados en Zenodo.
  - 19 estudios de prueba, publicados aparte y anotados por dos evaluadores.
- **Secuencia usada:** solo T2 ponderada (T2w). No se usaron DWI ni ADC.
- **Etiquetas:** 0 = fondo, 1 = glándula central (zona de transición), 2 = zona periférica.

### Cómo se entrenó

- **Arquitectura:** U-Net 3D de MONAI (`monai.networks.nets.UNet`).
  - Entrada de 1 canal y salida de 3 clases.
  - Canales 16-32-64-128-256-512, pasos de 2 y 4 unidades residuales por nivel.
  - Normalización por lotes, activación PReLU y *dropout* de 0,15.
- **Tarea:** clasificación de cada vóxel en fondo, glándula central o zona periférica.
- **Función de pérdida:** *focal soft-Dice*, optimizada por descenso de gradiente.
- **Entrada:** parches de 96 × 96 × 96 vóxeles con intensidad escalada a [0, 1].
- **Preprocesamiento de los autores:**
  - Recorte centrado del campo de visión: el FOV axial original es de 180 mm y la próstata rara vez supera los 100 mm.
  - Remuestreo; el T2w original es de 0,47 × 0,47 × 3 mm.
- **Desempeño publicado:** sobre la prueba de Prostate158.

| Métrica | Zona de transición (evaluador 1 / 2) | Zona periférica (evaluador 1 / 2) |
|---|---|---|
| Dice | 0,877 / 0,875 | 0,754 / 0,730 |
| Distancia de Hausdorff (mm) | 18,3 / 17,5 | 22,8 / 33,2 |
| Distancia de superficie (mm) | 2,19 / 2,59 | 1,95 / 1,88 |

Fuente: `modelos/prostate_mri_anatomy/docs/README.md` y `configs/metadata.json`, que se descargan con el modelo. Artículo de referencia:

> Adams, L. C., Makowski, M. R., Engel, G., Rattunde, M., Busch, F., Asbach, P., … & Bressem, K. K. (2022). Prostate158 – An expert-annotated 3T MRI dataset and algorithm for prostate cancer detection. *Computers in Biology and Medicine, 148*, 105817. https://doi.org/10.1016/j.compbiomed.2022.105817

### Cómo lo usa Prosta-AI

- **Preprocesamiento:** el mismo de la configuración de inferencia del modelo (RF-09). Orientación RAS, espaciado de 0,5 mm, `ScaleIntensity` y `NormalizeIntensity`. Los parámetros están en `modelos/prostate_mri_anatomy/preparacion.json`.
- **Inferencia:** por ventana deslizante de 96³, con `sw_batch_size` 4 y solapamiento de 0,5.
- **Posprocesado:** se conserva el componente conexo más grande de cada etiqueta.
- **Máscara de próstata:** es la unión de las etiquetas > 0. La ROI no distingue zonas.
- **Evaluación propia:** en MSD Task05 (división por paciente, semilla 2026) da un Dice medio de 0,8925 ± 0,034 en los 5 casos de prueba. Detalle y limitaciones en `reports/evaluacion/`.

## 3. Licencias y derechos de uso

| Componente | Licencia | Qué permite | Qué exige | Cómo se cumple en Prosta-AI |
|---|---|---|---|---|
| Pesos y configuración de `prostate_mri_anatomy` | Apache 2.0 | Usar, modificar y redistribuir, incluso con fines comerciales | Conservar el aviso de copyright y el texto de la licencia; indicar cambios si se redistribuye modificado | Los pesos no se versionan en git: `scripts/descargar_modelo.py` los descarga junto con su `LICENSE` y genera `FICHA.md` con autoría y cita |
| Datos de entrenamiento del modelo (Prostate158) | Zenodo lo publica como acceso abierto sin indicar una licencia concreta. El sitio del reto (prostate158.grand-challenge.org) exige un acuerdo de uso para investigación | Uso personal en investigación no comercial | No redistribuir los datos, no crear obras derivadas de los datos, no usarlos para diagnóstico ni atención de pacientes, no intentar reidentificar | Prosta-AI **no descarga, no guarda y no redistribuye** Prostate158. Solo usa los pesos que publicaron los mismos autores del conjunto bajo Apache 2.0 |
| Datos de ejemplo y de evaluación (MSD Task05_Prostate) | CC BY-SA 4.0 | Usar, adaptar y compartir, incluso con fines comerciales | Atribución, y compartir bajo la misma licencia lo que se derive de los datos | Los datos no se versionan (`datos/` está en `.gitignore`). Se cita en `README.md`, en `datos/FUENTE.md` y en los informes. Los informes publican solo métricas, no imágenes |
| MONAI | Apache 2.0 | Uso libre | Conservar avisos | Dependencia instalada, no modificada |
| PyTorch | BSD (3 cláusulas) | Uso libre | Conservar avisos | Dependencia instalada, no modificada |
| Fuente DejaVu Sans (texto del PNG exportado) | Licencia libre de Bitstream Vera / DejaVu | Uso y redistribución | Conservar el aviso | Incluido en `backend/prosta_ai/recursos/DejaVuSans-LICENCIA.txt` |

## 4. Riesgos y conclusión

**Conclusión:** el modelo **se puede usar** en Prosta-AI tal como está planteado. El proyecto es académico, no comercial y no clínico, y no redistribuye datos de pacientes.

| Riesgo | Nivel | Explicación | Respuesta |
|---|---|---|---|
| Restricciones heredadas de Prostate158 | Bajo para uso académico | Los pesos tienen licencia Apache 2.0, pero se entrenaron con datos cuyo acuerdo del reto limita el uso a investigación no comercial. Que un modelo entrenado sea «obra derivada» de los datos no está resuelto jurídicamente. Los propios autores del conjunto publicaron los pesos como licencia abierta, lo que indica su consentimiento | Mantener el uso académico y no comercial. Si el proyecto pasara a uso comercial, consultar a los autores o entrenar con datos de licencia compatible |
| Uso clínico | Fuera de alcance | Los autores del modelo y del conjunto lo excluyen expresamente | La aplicación muestra el aviso experimental en todas las pantallas de resultados y en el PNG exportado. El asistente rechaza preguntas clínicas |
| Atribución | Bajo | Apache 2.0 y CC BY-SA 4.0 exigen reconocer la autoría | Se cita en `README.md`, en este documento, en `FICHA.md` y en los informes de evaluación. Incluir las citas en la presentación final |
| Compartir bajo la misma licencia (CC BY-SA) | Bajo | Afectaría a material derivado de Task05 que se publique, por ejemplo imágenes con la ROI o un modelo ajustado con Task05 | Si se publican capturas con imágenes de Task05 o un modelo ajustado con ellas, hacerlo bajo CC BY-SA 4.0 y con atribución |
| Sobreestimación de métricas | Medio (técnico, no legal) | No se puede descartar que el preentrenamiento haya visto datos parecidos a Task05 | Documentado en el informe de evaluación |
| Cambio de la fuente | Bajo | El modelo se descarga de Hugging Face | La revisión está fijada y el hash SHA-256 se verifica en la ficha |

**Obligaciones del equipo:**
1. Mantener `LICENSE` y `FICHA.md` junto a los pesos si alguna vez se redistribuyen.
2. Citar el modelo, Prostate158 y el Medical Segmentation Decathlon en la documentación final y en la presentación.
3. No subir al repositorio imágenes ni máscaras de los conjuntos de datos.
4. No presentar la aplicación como herramienta de diagnóstico.

Referencias de licencias:
- Apache 2.0: https://www.apache.org/licenses/LICENSE-2.0
- CC BY-SA 4.0: https://creativecommons.org/licenses/by-sa/4.0/
- Acuerdo de uso de Prostate158: https://prostate158.grand-challenge.org/data/

Licencias consultadas el 04/11/2026.
