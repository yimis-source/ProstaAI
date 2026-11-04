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
| prostate_17 | 0.9097 | 0.8344 | 13.1 |
| prostate_28 | 0.8320 | 0.7123 | 8.7 |
| prostate_34 | 0.9105 | 0.8356 | 10.0 |
| prostate_44 | 0.9090 | 0.8332 | 21.5 |
| **Media ± desv.** | **0.8925 ± 0.0340** | **0.8071 ± 0.0534** | **13.3 ± 5.0** |

## Comparación con la meta (RF-24)

Se **cumple** la meta (Dice medio 0.8925 >= 0.80).
El caso más bajo es prostate_28 (Dice 0.8320).

## Limitaciones

- **Posible sesgo (sobreestimación) por datos de entrenamiento.** Según la documentación del bundle (`configs/metadata.json`, campo `data_source`: "Prostate158 from 10.5281/zenodo.6481141"; `docs/README.md`: "The model was trained in the prostate158 training data ... Only T2w images were used for this task"), el modelo preentrenado se entrenó con Prostate158 y la documentación no menciona MSD Task05 ni como entrenamiento ni como validación. Por tanto no hay evidencia documentada de solapamiento, pero tampoco se puede garantizar que los datos de Task05 estén ausentes de su preentrenamiento ni de la fuente de Prostate158 (el bundle no incluye la lista de casos ni las semillas). Si hubiera solapamiento, la evaluación sobre Task05 estaría sobreestimada. Además, la división 70/15/15 de este proyecto es independiente de cualquier división usada por los autores del bundle, así que los casos de prueba de aquí no son, por construcción, 'no vistos' por ese modelo. Las cifras del propio bundle (Dice de glándula central 0,88 y zona periférica 0,75) son sobre el conjunto de prueba de Prostate158, no de Task05.
- Con solo 5 casos de prueba la media tiene mucha incertidumbre; un caso malo mueve mucho el promedio (ver la desviación típica).
- Cambio de dominio: los pesos se entrenaron con Prostate158 (T2, 3 T, hospital distinto) y Task05 tiene cortes gruesos (4 mm), otra resolución y otro protocolo; el remuestreo a 0,5 mm es por interpolación y no añade detalle.
- Las etiquetas de Task05 son zona periférica y de transición; la próstata completa es su unión, mientras el modelo se entrenó para dos zonas. Los criterios de delimitación de los anotadores pueden diferir (p. ej. en base y ápex).
- Un solo conjunto público y un solo observador por caso (sin variabilidad entre observadores).
- Las métricas de superficie (Hausdorff, etc.) no se calculan; solo Dice e IoU.
- Los tiempos dependen del equipo; no representan el rendimiento en otro hardware.
- No hay validación clínica ni externa a estos datos públicos.
