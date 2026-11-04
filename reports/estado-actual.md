# Estado actual — Prosta-AI (2026-11-03)

Rama de trabajo: `desarrollo` (creada desde `main`), pendiente de revisión por el equipo antes de integrarse a `main`.

## Qué funciona (verificado)
- **Flujo completo CU01–CU05 en el navegador contra el backend real** (PostgreSQL + modelo real): primer acceso con alias → carga NIfTI + referencia → «Procesar» → 5 etapas con estado y tiempo → visor con y sin ROI, Dice/IoU → Mis estudios. Sin errores de consola.
- **CU06** asistente por reglas; ante preguntas clínicas declina y remite a un profesional.
- **DICOM** (.zip con serie) con datos de paciente falsos: se procesa (Dice 0,915) y no queda ningún dato personal en el almacenamiento, ni tras reprocesar.
- **Rechazo** de formatos no admitidos con mensaje claro; el estudio queda como «no compatible».
- **Rendimiento** (RR-01, ≤ 120 s): 10–25 s por estudio en CPU (Ryzen 5 5600G, sin GPU).
- **Evaluación** (RF-23/24): Dice medio 0,8925 ± 0,034, IoU 0,807 en el conjunto de prueba de Task05 (5 casos, división por paciente); sobre los 32 casos, 0,874 ± 0,122. Informes en `reports/evaluacion/`. El caso atípico prostate_07 (Dice 0,226) está analizado: falso positivo grande en el borde de la imagen.
- **Pruebas**: `cd backend && .venv/bin/pytest` en verde (330 pruebas); `cd frontend && npm run build` sin errores.
- Interfaz fiel al diseño de `docs/ejecucion/assets/pantallas/`, adaptada a < 768 px.

## Correcciones hechas durante la integración
- El `.zip` DICOM original (con datos de persona) quedaba guardado tras desidentificar su contenido → ahora se borra; si no se puede desidentificar, se eliminan los archivos del estudio. Pruebas añadidas.
- El aviso exportado en PNG no mostraba tildes → se incluye la fuente DejaVu Sans (licencia libre) en `backend/prosta_ai/recursos/`.
- Color de la ROI alineado con el diseño (verde azulado).
- `create_strategy` ahora acepta modelos propios con cualquier nombre si su carpeta tiene `preparacion.json` (para usar pesos entrenados en Colab con `PROSTA_MODELO_NOMBRE`).
- Choque de módulos `conftest` entre suites de pruebas → utilidades movidas a `backend/tests/apoyo_api.py`.
- El asistente de uso respondía con la primera palabra clave que coincidía (12 de 22 preguntas de prueba caían en el mensaje genérico, varias recibían una respuesta equivocada y algunas preguntas de salud personal no se bloqueaban) → se reescribió como paquete `assistant/` con base de conocimiento curada, puntuación por coincidencia, filtro clínico ampliado, consultas sobre los estudios del propio usuario y respuestas con pasos, enlace y sugerencias. Sigue siendo determinista y sin red. Suite de casos definidos en `backend/tests/test_asistente.py`.
- El `.gitignore` se había perdido al cambiar de rama → restaurado y ampliado.
- El pipeline se reconstruía en cada trabajo y releía los pesos del disco → ahora se construye una vez y se reutiliza.

## Decisiones técnicas por validar con el equipo
1. **Modelo** (decidido por el equipo el 04/11/2026): se usa por ahora el bundle MONAI preentrenado `prostate_mri_anatomy` (Apache 2.0, entrenado con Prostate158). Licencias y riesgos revisados en `docs-tecnicos/modelo-y-licencias.md`: apto para uso académico, no comercial y no clínico. El ajuste en Colab (`entrenamiento/`) queda como mejora posterior.
2. **Datos de ejemplo**: MSD Task05_Prostate (CC-BY-SA 4.0). Era una decisión pendiente del equipo.
3. **Límite de carga**: 500 MB (`PROSTA_MAX_UPLOAD_MB`).
4. **Máscara de referencia**: se sube opcionalmente junto al estudio; se distingue por carpeta (`referencia/`) sin cambiar el modelo de datos.
5. **Reintento** = trabajo nuevo para el mismo estudio (el diagrama decía «vuelve a pendiente»; el modelo de datos 1:N lo permite).
6. **PostgreSQL local de usuario** en el puerto 5433 (`scripts/postgres_local.sh`), porque el servicio del sistema requiere sudo.
7. `modelo.ruta_pesos`, `hash_pesos` y `ruta_configuracion` admiten nulos (para registrar el modelo aunque falten los pesos).
8. Un estudio rechazado se registra como «no compatible» sin guardar sus archivos (para que aparezca en Mis estudios).

## Riesgos y pendientes
- **Ventana de privacidad**: un DICOM queda en el almacenamiento con sus datos originales entre la carga y el inicio del procesamiento (la arquitectura ubica la desidentificación en la tarea). Si se quiere eliminar del todo, mover `deidentify_dicom` a la admisión.
- El aviso de evaluación sobre posible sesgo por datos de entrenamiento está documentado en el informe.
- La clave `PROSTA_SECRET_KEY` de `.env.example` es de ejemplo; `scripts/instalar.sh` genera una aleatoria.
- **Ajuste ligero del modelo** (Acta riesgo 1, matriz req. 3.4): pospuesto por decisión del equipo; preparado en `entrenamiento/` y no ejecutado. El cuaderno de Colab clona el repositorio, así que requiere publicar la rama. Regla de adopción: usar el modelo ajustado si su Dice en el conjunto de prueba es ≥ 0,8925; si no, conservar el preentrenado y documentarlo.
- Pendiente del equipo: actualizar la inconsistencia I-08 (la API ya está definida en `docs-tecnicos/especificacion-tecnica.md`) e I-02 (el botón dice «Procesar» en la aplicación).

## Cómo retomar
```bash
scripts/instalar.sh   # solo la primera vez
scripts/arrancar.sh   # http://localhost:5173
```
Usuario de prueba ya creado: alias `prueba_e2e`, contraseña `clave12345` (solo en la base local).
