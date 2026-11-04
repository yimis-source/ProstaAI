# Evaluación del modelo `prostate_mri_anatomy` (2026-11-03)

Uso académico y experimental; no es una evaluación clínica ni diagnóstica.

## Condiciones

- Modelo: prostate_mri_anatomy, versión 0.3.6.
- SHA-256 de los pesos: `3c18e4c658bb088f551b1d63219ef8340fe6256d016c75fc140d3da49dda696d`.
- Ruta de ejecución: `build_pipeline` (la misma que la aplicación), imagen = canal 0 (T2) del NIfTI 4D, referencia = etiquetas > 0 (zona periférica + zona de transición).
- Métricas calculadas en la rejilla de la imagen original (máscara devuelta al espacio original).
- Dispositivo: cpu. Hardware: AMD Ryzen 5 5600G with Radeon Graphics; 6 hilos de torch; sin GPU (CPU); Linux 7.2.14-arch1-1.
- Software: Python 3.12.14, torch 2.5.1+cpu, MONAI 1.4.0.
- División: `entrenamiento/division_task05.json`, semilla 2026, {'entrenamiento': 22, 'validacion': 5, 'prueba': 5}, huella `728fae869f02e7c7…`.
- Conjunto evaluado: prueba (5 casos: prostate_13, prostate_17, prostate_28, prostate_34, prostate_44).
- Tiempo por caso: todo el pipeline (lectura, preparación, segmentación, paso al espacio original), incluida la carga de los pesos, que se hace una sola vez en el primer caso.
- Desviación: típica muestral (n-1).

## Resultados sobre el conjunto de prueba

| Caso | Dice | IoU | Tiempo (s) |
|---|---:|---:|---:|
| prostate_13 | 0.9012 | 0.8201 | 13.3 |
| prostate_17 | 0.9097 | 0.8344 | 13.0 |
| prostate_28 | 0.8320 | 0.7123 | 10.3 |
| prostate_34 | 0.9105 | 0.8356 | 9.8 |
| prostate_44 | 0.9090 | 0.8332 | 13.7 |
| **Media ± desv.** | **0.8925 ± 0.0340** | **0.8071 ± 0.0534** | **12.0 ± 1.8** |

## Comparación con la meta (RF-24)

Se **cumple** la meta (Dice medio 0.8925 >= 0.80).
El caso más bajo es prostate_28 (Dice 0.8320).

## Dato adicional: los 32 casos de Task05

| Caso | Dice | IoU | Tiempo (s) |
|---|---:|---:|---:|
| prostate_00 | 0.8786 | 0.7835 | 18.2 |
| prostate_01 | 0.9178 | 0.8481 | 21.0 |
| prostate_02 | 0.9056 | 0.8274 | 19.4 |
| prostate_04 | 0.9154 | 0.8440 | 11.6 |
| prostate_06 | 0.9040 | 0.8248 | 13.5 |
| prostate_07 | 0.2255 | 0.1271 | 15.8 |
| prostate_10 | 0.8080 | 0.6778 | 14.0 |
| prostate_13 | 0.9012 | 0.8201 | 13.3 |
| prostate_14 | 0.8866 | 0.7962 | 19.8 |
| prostate_16 | 0.9380 | 0.8832 | 18.6 |
| prostate_17 | 0.9097 | 0.8344 | 13.0 |
| prostate_18 | 0.9155 | 0.8442 | 13.4 |
| prostate_20 | 0.9241 | 0.8590 | 13.9 |
| prostate_21 | 0.8945 | 0.8091 | 13.7 |
| prostate_24 | 0.9239 | 0.8586 | 13.8 |
| prostate_25 | 0.9006 | 0.8192 | 23.4 |
| prostate_28 | 0.8320 | 0.7123 | 10.3 |
| prostate_29 | 0.9136 | 0.8409 | 10.4 |
| prostate_31 | 0.8662 | 0.7640 | 13.5 |
| prostate_32 | 0.8394 | 0.7233 | 13.4 |
| prostate_34 | 0.9105 | 0.8356 | 9.8 |
| prostate_35 | 0.9019 | 0.8213 | 13.8 |
| prostate_37 | 0.8971 | 0.8134 | 10.3 |
| prostate_38 | 0.9255 | 0.8613 | 13.5 |
| prostate_39 | 0.8980 | 0.8149 | 10.2 |
| prostate_40 | 0.8722 | 0.7734 | 13.4 |
| prostate_41 | 0.9317 | 0.8722 | 9.9 |
| prostate_42 | 0.9145 | 0.8424 | 19.1 |
| prostate_43 | 0.8767 | 0.7804 | 13.2 |
| prostate_44 | 0.9090 | 0.8332 | 13.7 |
| prostate_46 | 0.8322 | 0.7126 | 13.2 |
| prostate_47 | 0.8863 | 0.7958 | 13.2 |
| **Media ± desv.** | **0.8736 ± 0.1222** | **0.7892 ± 0.1304** | **14.3 ± 3.4** |

## Limitaciones

- **Posible sesgo (sobreestimación) por datos de entrenamiento.** Según la documentación del bundle (`configs/metadata.json`, campo `data_source`: "Prostate158 from 10.5281/zenodo.6481141"; `docs/README.md`: "The model was trained in the prostate158 training data ... Only T2w images were used for this task"), el modelo preentrenado se entrenó con Prostate158 y la documentación no menciona MSD Task05 ni como entrenamiento ni como validación. Por tanto no hay evidencia documentada de solapamiento, pero tampoco se puede garantizar que los datos de Task05 estén ausentes de su preentrenamiento ni de la fuente de Prostate158 (el bundle no incluye la lista de casos ni las semillas). Si hubiera solapamiento, la evaluación sobre Task05 estaría sobreestimada. Además, la división 70/15/15 de este proyecto es independiente de cualquier división usada por los autores del bundle, así que los casos de prueba de aquí no son, por construcción, 'no vistos' por ese modelo. Las cifras del propio bundle (Dice de glándula central 0,88 y zona periférica 0,75) son sobre el conjunto de prueba de Prostate158, no de Task05.
- Con solo 5 casos de prueba la media tiene mucha incertidumbre; un caso malo mueve mucho el promedio (ver la desviación típica).
- Cambio de dominio: los pesos se entrenaron con Prostate158 (T2, 3 T, hospital distinto) y Task05 tiene cortes gruesos (4 mm), otra resolución y otro protocolo; el remuestreo a 0,5 mm es por interpolación y no añade detalle.
- Las etiquetas de Task05 son zona periférica y de transición; la próstata completa es su unión, mientras el modelo se entrenó para dos zonas. Los criterios de delimitación de los anotadores pueden diferir (p. ej. en base y ápex).
- Un solo conjunto público y un solo observador por caso (sin variabilidad entre observadores).
- Las métricas de superficie (Hausdorff, etc.) no se calculan; solo Dice e IoU.
- Los tiempos dependen del equipo; no representan el rendimiento en otro hardware.
- No hay validación clínica ni externa a estos datos públicos.

## Análisis del caso atípico prostate_07 (Dice 0,226)

La geometría del caso es normal (320×320×20, 0,62×0,62×3,6 mm, RAS) y su próstata es pequeña (11 399 vóxeles frente a 32 846 del caso 00). El modelo sí delimita la glándula: la componente conexa centrada en (157, 157, 13) tiene 6 097 vóxeles, de los cuales 4 792 coinciden con la referencia. Además predice una región falsa de 24 225 vóxeles en el borde del campo de visión (tejido graso, centro en (270, 21, 11)). Como el posproceso del bundle conserva la componente más grande de cada zona, esa región falsa desplaza a la glándula en una de las zonas y el Dice cae.

Es un fallo del modelo preentrenado ante el cambio de dominio, no de la ruta de inferencia. Posibles mejoras, a evaluar con el conjunto de validación y no con el de prueba: ajuste fino con Task05 (`entrenamiento/entrenar.py`) o un posproceso que prefiera la componente más cercana al centro del campo de visión. Cualquiera de ellas debe documentarse y aplicarse igual en entrenamiento, evaluación e inferencia.
