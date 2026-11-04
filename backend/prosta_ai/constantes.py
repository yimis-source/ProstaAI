"""Constantes compartidas por la API y el procesamiento."""

AVISO_EXPERIMENTAL = (
    "Resultado experimental con fines académicos. No es un diagnóstico ni "
    "sustituye la valoración de un profesional de la salud."
)

# Estados de estudios y trabajos (coinciden con los CHECK de la base de datos)
FORMATOS = ("DICOM", "NIfTI")
ADMISION = ("admitido", "no compatible")
ESTADOS_TRABAJO = ("pendiente", "en proceso", "completado", "fallido")

PENDIENTE, EN_PROCESO, COMPLETADO, FALLIDO = ESTADOS_TRABAJO
ADMITIDO, NO_COMPATIBLE = ADMISION
LISTO_PARA_PROCESAR = "listo para procesar"

MENSAJE_ERROR_GENERICO = (
    "Ocurrió un error inesperado durante el procesamiento. "
    "Intente de nuevo más tarde."
)
