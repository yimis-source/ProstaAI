"""Base de conocimiento del asistente de uso (CU06).

Cada tema es una respuesta fija y revisada: no se genera texto. Todo lo que
aquí se describe (menús, botones, formatos, límites, etapas) corresponde a la
aplicación tal como está construida. No hay contenido clínico (RF-20 a RF-22).
"""
from dataclasses import dataclass, field

Frase = str | tuple[str, float]

NOTA_ROI = (
    "La ROI es una salida experimental: puede ser imprecisa y no implica un hallazgo. "
    "Mi ayuda se limita al uso de la app."
)


@dataclass(frozen=True)
class Tema:
    id: str
    titulo: str
    sugerencia: str  # pregunta modelo: se ofrece como sugerencia y debe resolver a este tema
    frases: list[Frase]
    intro: str
    pasos: list[str] = field(default_factory=list)
    nota: str | None = None
    enlace: dict | None = None
    relacionados: list[str] = field(default_factory=list)


RUTAS_VALIDAS = ("/", "/cargar", "/procesamiento", "/roi", "/estudios", "/asistente")

TEMAS: list[Tema] = [
    # ---------------------------------------------------------------- conversación
    Tema(
        id="saludo", titulo="Saludo", sugerencia="Hola, ¿qué puedes hacer?",
        frases=["hola", "buenas", "buenos dias", "buenas tardes", "buenas noches", "saludos", "hey",
                "que tal"],
        intro="¡Hola! Soy el asistente de uso de Prosta-AI. Te oriento sobre cómo usar la aplicación.",
        pasos=[
            "Cargar un estudio de prueba y, si quieres, su máscara de referencia.",
            "Procesarlo y seguir el estado de cada etapa.",
            "Comparar la imagen original con la ROI y exportar una imagen.",
        ],
        nota="Dime qué quieres hacer o elige una de las preguntas de abajo.",
        relacionados=["primeros_pasos", "flujo", "asistente"],
    ),
    Tema(
        id="gracias", titulo="Agradecimiento", sugerencia="Gracias",
        frases=["gracias", "muchas gracias", "mil gracias", "genial", "perfecto", "excelente",
                "muy amable", "entendido", "listo gracias", "vale gracias"],
        intro="¡De nada! Me alegra poder ayudarte con la aplicación.",
        nota="Si te surge otra duda sobre el uso de Prosta-AI, pregúntame cuando quieras.",
        relacionados=["flujo", "comparar_roi", "metricas"],
    ),
    Tema(
        id="despedida", titulo="Despedida", sugerencia="Adiós, hasta luego",
        frases=["adios", "chao", "chau", "hasta luego", "hasta pronto", "nos vemos", "bye", "me voy",
                "hasta manana"],
        intro="¡Hasta pronto! Cuando termines, puedes cerrar tu sesión desde el menú lateral.",
        nota="Aquí estaré si necesitas ayuda con la aplicación.",
        relacionados=["cerrar_sesion", "privacidad"],
    ),
    # ---------------------------------------------------------------- qué es y flujo
    Tema(
        id="que_es", titulo="Qué es Prosta-AI", sugerencia="¿Qué es Prosta-AI?",
        frases=[("que es prosta ai", 1.5), "para que sirve prosta ai", "para que sirve la aplicacion",
                "de que trata la aplicacion", "que hace prosta ai", "que hace la app",
                "que es esta aplicacion", "quienes son ustedes", "para que sirve esta app",
                "objetivo de la aplicacion", "que es una resonancia magnetica",
                "para que sirve esto", "que hace esto", "prosta ai"],
        intro="Prosta-AI es una aplicación web académica y experimental para explorar la segmentación "
              "de resonancias magnéticas de próstata públicas y desidentificadas.",
        pasos=[
            "Cargas un estudio de prueba en formato DICOM o NIfTI.",
            "Un modelo de segmentación propone una región de interés (ROI) sobre cada corte.",
            "Comparas la imagen original con la ROI y, si subiste una máscara de referencia, ves Dice e IoU.",
        ],
        nota="No es un dispositivo médico ni ofrece diagnóstico: es una herramienta de laboratorio. "
             "Mi ayuda se limita al uso de la app.",
        enlace={"ruta": "/", "texto": "Ir a Inicio"},
        relacionados=["flujo", "primeros_pasos", "limitaciones"],
    ),
    Tema(
        id="flujo", titulo="Cómo funciona el flujo completo", sugerencia="¿Cómo funciona la aplicación?",
        frases=[("como funciona", 1.5), "como funciona la aplicacion", "como funciona prosta ai",
                "como se usa la aplicacion", "flujo de trabajo", "flujo completo",
                "paso a paso de la aplicacion", "resumen del proceso", "como se usa",
                "como uso la aplicacion", "como trabaja la app", "explicame como funciona",
                "de que consta el flujo", "que se hace en cada seccion"],
        intro="El flujo tiene tres pasos, que también verás arriba en cada pantalla (Cargar, Procesar, Visualizar):",
        pasos=[
            "En «Cargar estudios» subes los archivos de un estudio de prueba (y, si quieres, su máscara de "
            "referencia). Se le asigna un ID anónimo.",
            "En «Procesamiento» eliges el estudio y pulsas «Procesar»; se ejecutan cinco etapas: control de "
            "calidad, preparación, segmentación, ROI y evaluación.",
            "En «Visualizar ROI» comparas el corte original con el corte con la ROI superpuesta, miras "
            "Dice e IoU (si hay referencia) y puedes exportar una imagen.",
            "En «Mis estudios» consultas el historial y puedes eliminar lo que ya no necesites.",
        ],
        nota="Los resultados son experimentales. Mi ayuda se limita al uso de la app.",
        enlace={"ruta": "/cargar", "texto": "Ir a Cargar estudios"},
        relacionados=["etapas", "cargar", "comparar_roi"],
    ),
    Tema(
        id="primeros_pasos", titulo="Primeros pasos", sugerencia="¿Qué hago primero?",
        frases=[("que hago primero", 1.5), "por donde empiezo", "como empiezo", "como comenzar",
                "primeros pasos", "empezar a usar", "por donde comienzo", "que debo hacer primero",
                "no se que hacer", "no se por donde empezar", "que sigue", "cual es el primer paso",
                "estoy perdido", "guiame", "quiero empezar", "que hago ahora", "como arranco"],
        intro="Para empezar, sigue este orden:",
        pasos=[
            "Entra a «Cargar estudios» y pulsa «Seleccionar archivos» (o arrástralos) con un estudio de "
            "prueba. Si no tienes uno, puedes descargar datos públicos de ejemplo.",
            "Opcional: añade la máscara de referencia para obtener Dice e IoU.",
            "Pulsa «Cargar estudio» y luego «Continuar a procesamiento».",
            "En «Procesamiento» pulsa «Procesar» y espera a que terminen las cinco etapas.",
            "Pulsa «Ver resultados» para comparar la ROI con la imagen original.",
        ],
        nota="Usa solo archivos de prueba sin datos personales. Mi ayuda se limita al uso de la app.",
        enlace={"ruta": "/cargar", "texto": "Ir a Cargar estudios"},
        relacionados=["datos_prueba", "formatos", "procesar"],
    ),
    Tema(
        id="menu", titulo="Navegar por la aplicación", sugerencia="¿Qué secciones tiene el menú?",
        frases=["secciones del menu", "menu lateral", "como navego", "navegar por la aplicacion",
                "donde esta cada cosa", "paginas de la aplicacion", "que opciones hay",
                "donde encuentro", "como llego a", "que hay en el menu", "pantallas de la aplicacion",
                "navegacion", "como me muevo por la app"],
        intro="El menú lateral («Espacio de trabajo») tiene estas secciones:",
        pasos=[
            "Inicio: resumen, tus últimos estudios y accesos rápidos.",
            "Cargar estudios: subir los archivos de un estudio de prueba.",
            "Procesamiento: ejecutar el flujo y ver el estado de cada etapa.",
            "Visualizar ROI: comparar la imagen original con la ROI.",
            "Mis estudios: historial, filtros y eliminación.",
            "Asistente IA: esta ayuda de uso. Al final del menú está «Cerrar sesión».",
        ],
        nota="En pantallas pequeñas, el menú se abre con el botón de la barra superior.",
        relacionados=["flujo", "mis_estudios", "cerrar_sesion"],
    ),
    # ---------------------------------------------------------------- acceso
    Tema(
        id="acceso", titulo="Acceso y primera vez", sugerencia="¿Cómo accedo la primera vez?",
        frases=["como accedo", "como entro", "como inicio sesion", "primera vez", "acceder por primera vez",
                "crear cuenta", "registrarme", "registro de usuario", "como me registro",
                "usuario y contrasena", "iniciar sesion", "login", "contrasena", "olvide mi contrasena",
                "recuperar contrasena", "no puedo entrar", "no puedo acceder", "confirmar contrasena",
                "usuario academico", "alias", "cambiar mi contrasena"],
        intro="El acceso se hace en dos pasos desde la pantalla «Accede a Prosta-AI»:",
        pasos=[
            "Escribe tu usuario (entre 3 y 30 caracteres: letras, números, punto, guion o guion bajo) y pulsa «Continuar».",
            "Si el usuario ya existe, escribe tu contraseña y pulsa «Acceder».",
            "Si es la primera vez, la app te pide crear una contraseña de al menos 8 caracteres y confirmarla; "
            "luego pulsa «Acceder por primera vez». Desde entonces el usuario queda reconocido.",
        ],
        nota="No hay registro de cuentas ni recuperación de contraseña en la pantalla de acceso. "
             "Si la olvidas, no puedo restablecerla; usa un usuario nuevo con archivos de prueba.",
        relacionados=["cerrar_sesion", "privacidad", "primeros_pasos"],
    ),
    Tema(
        id="cerrar_sesion", titulo="Cerrar sesión", sugerencia="¿Cómo cierro sesión?",
        frases=[("cerrar sesion", 1.5), "salir de la aplicacion", "como salgo", "cerrar mi sesion",
                "desconectarme", "logout", "terminar sesion", "salir de mi cuenta", "sesion vencida",
                "la sesion expiro", "me saca de la sesion", "cuanto dura la sesion"],
        intro="Para salir de forma segura:",
        pasos=[
            "Abre el menú lateral (en pantallas pequeñas, con el botón de la barra superior).",
            "Pulsa «Cerrar sesión», al final del menú.",
            "Si tu sesión vence (dura 8 horas), la app te pedirá ingresar de nuevo.",
        ],
        nota="Cerrar sesión no elimina tus estudios; siguen en «Mis estudios».",
        relacionados=["acceso", "mis_estudios"],
    ),
    # ---------------------------------------------------------------- carga
    Tema(
        id="cargar", titulo="Cargar un estudio", sugerencia="¿Cómo cargo un estudio?",
        frases=[("como cargo un estudio", 1.5), "como subo un archivo", "subir estudio", "cargar archivos",
                "cargar un estudio", "subir imagen", "como subo mis archivos", "donde subo los archivos",
                "arrastrar archivos", "seleccionar archivos", "boton cargar estudio",
                "adjuntar archivos", "importar estudio", "agregar un estudio", "nuevo estudio",
                "no me deja cargar", "id anonimo asignado", "como subo mi resonancia", "cargar una resonancia",
                "subir resonancia magnetica"],
        intro="Para cargar un estudio de prueba:",
        pasos=[
            "Ve a «Cargar estudios».",
            "Arrastra los archivos a la zona indicada o pulsa «Seleccionar archivos». Los que tengan un formato "
            "no admitido aparecen como «Excluido».",
            "Opcional: en «Máscara de referencia (opcional)» añade la máscara para calcular Dice e IoU.",
            "Pulsa «Cargar estudio». Se asigna un ID anónimo (por ejemplo EST-0001).",
            "Pulsa «Continuar a procesamiento» para seguir.",
        ],
        nota="Usa solo archivos de prueba sin datos personales. Si se rechaza, la app muestra el motivo.",
        enlace={"ruta": "/cargar", "texto": "Ir a Cargar estudios"},
        relacionados=["formatos", "mascara_subir", "procesar"],
    ),
    Tema(
        id="formatos", titulo="Formatos y tamaño", sugerencia="¿Qué formatos puedo cargar?",
        frases=[("que formatos puedo cargar", 1.5), "formatos admitidos", "formatos aceptados",
                "que formatos acepta", "que tipo de archivos", "tipos de archivo", "dicom", "nifti", "nii",
                "nii gz", "zip", "dcm", "extension de archivo", "tamano maximo", "limite de tamano",
                "cuanto pesa", "tamano de archivo", "archivo muy grande", "cuantos megas", "peso maximo",
                "puedo subir un zip", "puedo subir varios archivos", "que archivos sirven", "puedo usar dicom",
                "puedo usar nifti", "acepta dicom", "sirve dicom", "se puede usar nifti"],
        intro="Se admiten dos formatos de estudio:",
        pasos=[
            "NIfTI: un solo archivo .nii o .nii.gz.",
            "DICOM: varios archivos .dcm de la misma serie, o un único .zip con la serie.",
            "No se pueden combinar formatos en un mismo estudio (ni mezclar un .zip con archivos .dcm).",
            "El tamaño máximo por carga es de 500 MB (límite de la configuración por defecto).",
        ],
        nota="En DICOM, la app elimina los datos que identifican personas; si no puede hacerlo, rechaza el estudio.",
        enlace={"ruta": "/cargar", "texto": "Ir a Cargar estudios"},
        relacionados=["cargar", "rechazo_carga", "privacidad"],
    ),
    Tema(
        id="rechazo_carga", titulo="Estudio rechazado al cargar",
        sugerencia="¿Por qué se rechaza mi estudio al cargarlo?",
        frases=[("estudio rechazado", 1.5), "por que se rechaza mi estudio", "no compatible",
                "estudio no compatible", "formato no admitido", "archivo excluido", "excluido",
                "el estudio fue rechazado", "me rechaza el archivo", "no admite mi archivo",
                "archivo no valido", "no es un zip valido", "cabecera nifti invalida",
                "no se puede combinar formatos", "no compatible en mis estudios",
                "no tiene formato dicom valido"],
        intro="Un estudio se rechaza al cargarlo cuando no cumple las reglas de admisión. Revisa estos puntos:",
        pasos=[
            "El formato: NIfTI (.nii o .nii.gz, un solo archivo) o DICOM (.dcm varios, o un .zip con la serie).",
            "No mezcles formatos ni combines un .zip con archivos .dcm.",
            "Comprueba que los archivos no estén dañados (un .nii.gz debe estar comprimido con gzip) y que no "
            "superen los 500 MB.",
            "Si el DICOM no se puede desidentificar, el estudio se rechaza por seguridad.",
            "Corrige los archivos y vuelve a cargarlos en «Cargar estudios».",
        ],
        nota="Un estudio rechazado queda como «No compatible» en «Mis estudios» y no se puede procesar; "
             "puedes eliminarlo desde allí.",
        enlace={"ruta": "/cargar", "texto": "Ir a Cargar estudios"},
        relacionados=["formatos", "mis_estudios", "eliminar"],
    ),
    # ---------------------------------------------------------------- máscara de referencia
    Tema(
        id="mascara_que_es", titulo="Qué es la máscara de referencia",
        sugerencia="¿Qué es la máscara de referencia?",
        frases=[("que es la mascara de referencia", 1.5), "mascara de referencia", "que es la referencia",
                "para que sirve la mascara", "para que sirve la referencia", "ground truth",
                "segmentacion de referencia", "es obligatoria la mascara", "mascara opcional",
                "necesito la mascara", "referencia opcional", "mascara manual", "etiqueta de referencia"],
        intro="La máscara de referencia es un archivo NIfTI con la región ya delimitada (por ejemplo, de un "
              "conjunto público) que sirve como patrón de comparación.",
        pasos=[
            "Es opcional: puedes cargar un estudio y procesarlo sin ella.",
            "Debe tener la misma forma (mismas dimensiones) que la imagen del estudio.",
            "Con ella, la etapa de evaluación calcula Dice e IoU para medir cuánto coincide la ROI del modelo con la referencia.",
        ],
        nota="Dice e IoU miden coincidencia con la referencia, no el estado de salud de nadie.",
        enlace={"ruta": "/cargar", "texto": "Ir a Cargar estudios"},
        relacionados=["mascara_subir", "mascara_sin", "metricas"],
    ),
    Tema(
        id="mascara_subir", titulo="Cómo subir la máscara de referencia",
        sugerencia="¿Cómo subo la máscara de referencia?",
        frases=[("como subo la mascara de referencia", 1.5), "subir mascara", "cargar mascara",
                "adjuntar mascara", "añadir mascara", "como agrego la referencia", "subir la referencia",
                "donde pongo la mascara", "mascara de referencia nifti", "misma forma que la imagen",
                "formato de la mascara", "cargar la referencia"],
        intro="La máscara se sube junto con el estudio, en la misma pantalla:",
        pasos=[
            "En «Cargar estudios», baja a la tarjeta «Máscara de referencia (opcional)».",
            "Pulsa «Seleccionar archivos» o arrastra el archivo NIfTI de la máscara.",
            "Comprueba que tenga la misma forma que la imagen; si no, el control de calidad detendrá el procesamiento.",
            "Pulsa «Cargar estudio» como siempre.",
        ],
        nota="Si usas los datos de ejemplo, la máscara está en la carpeta labelsTr con el mismo nombre que la imagen.",
        enlace={"ruta": "/cargar", "texto": "Ir a Cargar estudios"},
        relacionados=["datos_prueba", "mascara_sin", "error_proceso"],
    ),
    Tema(
        id="mascara_sin", titulo="Qué pasa sin máscara de referencia",
        sugerencia="¿Qué pasa si no tengo máscara de referencia?",
        frases=[("que pasa si no tengo mascara de referencia", 1.5), "sin mascara de referencia",
                "sin referencia", "no tengo mascara", "no tengo referencia", "falta la mascara",
                "sin mascara", "dice no disponible", "por que no aparece dice", "no aparece el dice",
                "no sale el dice", "dice e iou no disponibles", "no hay metricas",
                "puedo procesar sin mascara", "por que no veo las metricas", "metricas no disponibles"],
        intro="Puedes procesar el estudio igualmente; solo cambia la parte de métricas:",
        pasos=[
            "La segmentación y la ROI se generan con normalidad y puedes compararlas en «Visualizar ROI».",
            "La etapa de evaluación no calcula Dice ni IoU, y la pantalla indica «No disponible: el estudio no "
            "tiene máscara de referencia».",
            "Para obtener las métricas, carga de nuevo el estudio incluyendo la máscara en «Máscara de referencia (opcional)».",
        ],
        nota="Sin referencia no hay forma de medir la coincidencia, pero la ROI se puede explorar igual.",
        enlace={"ruta": "/cargar", "texto": "Ir a Cargar estudios"},
        relacionados=["mascara_subir", "metricas", "comparar_roi"],
    ),
    Tema(
        id="datos_prueba", titulo="Datos de prueba públicos",
        sugerencia="¿De dónde saco imágenes de prueba?",
        frases=[("de donde saco imagenes de prueba", 1.5), "datos de prueba", "datos de ejemplo",
                "imagenes de ejemplo", "estudios de ejemplo", "donde consigo imagenes",
                "donde descargo estudios", "no tengo imagenes", "no tengo estudios para cargar",
                "conjunto de datos publico", "dataset", "msd", "task05", "task05 prostate",
                "medical segmentation decathlon", "archivos de prueba", "muestras de prueba",
                "descargar datos", "descargar ejemplos", "de donde saco archivos", "imagenes para probar"],
        intro="Puedes usar el conjunto público Medical Segmentation Decathlon, Task05_Prostate (licencia CC-BY-SA 4.0):",
        pasos=[
            "Desde la raíz del repositorio ejecuta: backend/.venv/bin/python scripts/descargar_datos_ejemplo.py",
            "Los datos quedan en la carpeta datos/ (con un archivo FUENTE.md con la licencia y la cita).",
            "Carga imagesTr/prostate_XX.nii.gz como estudio en «Cargar estudios».",
            "Si quieres Dice e IoU, carga labelsTr/prostate_XX.nii.gz como máscara de referencia.",
        ],
        nota="Son datos públicos y desidentificados. No uses imágenes de personas reales.",
        enlace={"ruta": "/cargar", "texto": "Ir a Cargar estudios"},
        relacionados=["cargar", "mascara_subir", "privacidad"],
    ),
    # ---------------------------------------------------------------- procesamiento
    Tema(
        id="procesar", titulo="Procesar un estudio", sugerencia="¿Cómo proceso un estudio?",
        frases=[("como proceso un estudio", 1.5), "como procesar", "procesar un estudio",
                "boton procesar", "iniciar el procesamiento", "ejecutar el procesamiento",
                "como segmento un estudio", "como se ejecuta el modelo", "pagina de procesamiento",
                "como empiezo el procesamiento", "lanzar el procesamiento", "estudio listo para procesar",
                "procesar de nuevo", "volver a procesar", "reprocesar",
                "se queda en pendiente", "esta en proceso"],
        intro="El procesamiento se lanza desde su propia pantalla:",
        pasos=[
            "Ve a «Procesamiento» y elige el estudio en el selector «Estudio» (los «No compatibles» no aparecen).",
            "Pulsa «Procesar». El estudio pasa a «Pendiente» y luego «En proceso».",
            "Mira el avance de las cinco etapas; la pantalla se actualiza sola cada 1,5 segundos.",
            "Al terminar pulsa «Ver resultados». Si quieres repetirlo, el botón cambia a «Procesar de nuevo» "
            "(o «Volver a procesar» si falló).",
        ],
        nota="Un estudio solo puede tener un procesamiento activo a la vez.",
        enlace={"ruta": "/procesamiento", "texto": "Ir a Procesamiento"},
        relacionados=["etapas", "tiempos", "error_proceso"],
    ),
    Tema(
        id="etapas", titulo="Las cinco etapas del procesamiento",
        sugerencia="¿Qué significa cada etapa del procesamiento?",
        frases=[("que significa cada etapa del procesamiento", 1.5), "etapas del procesamiento",
                "que etapas hay", "que hace cada etapa", "explicame las etapas", "cuales son las etapas",
                "control de calidad", "etapa de preparacion", "etapa de segmentacion", "etapa de roi",
                "etapa de evaluacion", "que es el control de calidad", "que es la preparacion",
                "que es la evaluacion", "5 etapas", "cinco etapas", "que pasa en cada etapa"],
        intro="El procesamiento ejecuta cinco etapas, siempre en este orden:",
        pasos=[
            "Control de calidad: verifica el formato y la estructura (volumen 3D con valores válidos, al menos 8 "
            "cortes y, si hay referencia, que tenga la misma forma que la imagen).",
            "Preparación: organiza las series y deja el volumen listo para el modelo.",
            "Segmentación: ejecuta el modelo experimental sobre el volumen.",
            "ROI: genera la región de interés que luego verás en el comparador.",
            "Evaluación: compara la ROI con la máscara de referencia (Dice e IoU), solo si la hay.",
        ],
        nota="Si una etapa falla, el procesamiento se detiene y la pantalla indica cuál fue y por qué.",
        enlace={"ruta": "/procesamiento", "texto": "Ir a Procesamiento"},
        relacionados=["procesar", "error_proceso", "tiempos"],
    ),
    Tema(
        id="tiempos", titulo="Cuánto tarda el procesamiento",
        sugerencia="¿Cuánto tarda el procesamiento?",
        frases=[("cuanto tarda el procesamiento", 1.5), "cuanto demora", "cuanto tiempo tarda",
                "tiempo de procesamiento", "es muy lento", "tarda mucho", "cuantos minutos",
                "tiempo estimado", "cuanto falta", "objetivo de tiempo", "tiempo transcurrido",
                "cuanto dura", "por que tarda tanto", "es lento", "velocidad del procesamiento",
                "ya van varios minutos", "se demora", "cuanto se demora el modelo"],
        intro="El tiempo depende de los archivos y de los recursos del equipo:",
        pasos=[
            "La pantalla «Procesamiento» muestra el «Tiempo transcurrido» y el tiempo de cada etapa.",
            "El objetivo de tiempo es de 2 minutos o menos; es una meta experimental, no una garantía.",
            "En un equipo sin GPU, la inferencia suele tardar entre 10 y 25 segundos por estudio.",
            "Mientras el estudio esté «En proceso», no hace falta que hagas nada: la pantalla se actualiza sola.",
        ],
        nota="Si pasa mucho tiempo sin avanzar, recarga la página; si el trabajo falló, verás la etapa y el motivo.",
        enlace={"ruta": "/procesamiento", "texto": "Ir a Procesamiento"},
        relacionados=["etapas", "procesar", "error_proceso"],
    ),
    Tema(
        id="error_proceso", titulo="Errores y etapa fallida",
        sugerencia="¿Por qué falló mi estudio?",
        frases=[("por que fallo mi estudio", 1.5), "el procesamiento fallo", "etapa fallida",
                "fallo el procesamiento", "me salio un error", "sale un error", "dio un error",
                "hubo un error", "mensaje de error", "no funciona", "no termina de procesar",
                "se detuvo el procesamiento", "ejecucion detenida", "estado fallido", "fallido",
                "que hago si falla", "que hago si hay un error", "como reintento", "se cayo",
                "problema al procesar", "error al procesar", "falla la segmentacion",
                "error en el control de calidad", "no se pudo leer el volumen", "volumen no valido",
                "algo salio mal", "no me funciona", "tengo un problema", "problemas con la app",
                ("no me deja procesar", 1.5), "no puedo procesar", "no se procesa", "no procesa",
                "el boton procesar no funciona"],
        intro="Cuando algo falla, la pantalla «Procesamiento» te dice en qué etapa y por qué. Así puedes actuar:",
        pasos=[
            "Abre «Procesamiento» y elige el estudio: verás un mensaje como «El procesamiento falló en la etapa …».",
            "Lee el motivo. Los más habituales son un volumen con menos de 8 cortes, valores no válidos o una "
            "referencia con forma distinta a la imagen (control de calidad).",
            "Corrige el problema. Si se debe a los archivos, carga de nuevo el estudio ya corregido.",
            "Si el estudio es correcto, pulsa «Volver a procesar» para intentarlo otra vez.",
        ],
        nota="Si vuelve a fallar con el mismo mensaje, prueba con otro estudio de prueba. "
             "Mi ayuda se limita al uso de la app.",
        enlace={"ruta": "/procesamiento", "texto": "Ir a Procesamiento"},
        relacionados=["etapas", "rechazo_carga", "formatos"],
    ),
    # ---------------------------------------------------------------- resultados
    Tema(
        id="ver_resultados", titulo="Dónde ver los resultados",
        sugerencia="¿Dónde veo los resultados?",
        frases=[("donde veo los resultados", 1.5), "ver resultados", "donde estan los resultados",
                "como veo el resultado", "donde veo la roi", "como veo la segmentacion",
                "abrir resultados", "ya termino donde veo", "acceder a los resultados", "ver la roi",
                "donde miro el resultado", "como abro el comparador", "visualizar roi",
                "boton ver resultados", "donde esta el comparador", "ver el resultado del estudio"],
        intro="Los resultados se consultan en «Visualizar ROI». Hay tres caminos:",
        pasos=[
            "Al terminar el procesamiento, pulsa «Ver resultados» en la pantalla «Procesamiento».",
            "Desde el menú, entra a «Visualizar ROI» y elige un estudio procesado.",
            "Desde «Mis estudios», pulsa «Ver ROI» en la fila del estudio completado.",
        ],
        nota="Solo se pueden ver resultados de estudios con estado «Completado».",
        enlace={"ruta": "/roi", "texto": "Ir a Visualizar ROI"},
        relacionados=["comparar_roi", "visor_controles", "exportar"],
    ),
    Tema(
        id="visor_controles", titulo="Controles del visor",
        sugerencia="¿Cómo cambio de corte o ajusto la opacidad?",
        frases=[("como cambio de corte o ajusto la opacidad", 1.5), "cambiar de corte", "cambio de corte",
                "ajustar la opacidad", "opacidad", "zoom", "acercar la imagen", "hacer zoom",
                "controles del visor", "controles del comparador", "deslizador de corte",
                "flechas del teclado", "ocultar la roi", "mostrar la roi", "interruptor roi",
                "restablecer zoom", "navegar entre cortes", "mover entre cortes", "ver otro corte",
                "como paso de corte", "transparencia", "agrandar la imagen", "slider", "desactivar la roi"],
        intro="En la barra «Controles del visor» tienes tres grupos de controles:",
        pasos=[
            "Corte: usa las flechas «Corte anterior» y «Corte siguiente» o el deslizador. También funcionan las "
            "flechas del teclado.",
            "ROI y Opacidad: el interruptor ROI muestra u oculta la superposición; el deslizador Opacidad "
            "(0 a 100 %) regula su transparencia y solo está activo con la ROI visible.",
            "Zoom: los botones − y + acercan o alejan entre 100 % y 300 %, y el botón de restablecer vuelve a 100 %.",
        ],
        nota="Corte y Zoom se aplican a los dos paneles a la vez, que están sincronizados. " + NOTA_ROI,
        enlace={"ruta": "/roi", "texto": "Ir a Visualizar ROI"},
        relacionados=["comparar_roi", "exportar", "metricas"],
    ),
    Tema(
        id="comparar_roi", titulo="Comparar la ROI con la imagen original",
        sugerencia="¿Cómo comparo la ROI con la imagen original?",
        frases=[("como comparo la roi con la imagen original", 1.5), "comparar la roi", "comparar con la original",
                "con y sin roi", "original mas roi", "dos paneles", "paneles del visor",
                "imagen original", "ver la imagen sin roi", "superposicion", "superponer la roi",
                "contorno teal", "como se ve la roi", "que es original mas roi", "diferencia entre los paneles",
                "visores sincronizados", "como contrasto la roi", "comparador de roi", "comparador",
                "que muestra cada panel", "roi sobre la imagen"],
        intro="En «Visualizar ROI» encontrarás dos paneles con el mismo corte de prueba:",
        pasos=[
            "Original muestra la imagen sin superposición.",
            "Original + ROI añade el contorno experimental en teal.",
            "Usa Corte y Zoom para ambos paneles; ajusta Opacidad o desactiva ROI para contrastar la imagen.",
        ],
        nota=NOTA_ROI,
        enlace={"ruta": "/roi", "texto": "Ir a Visualizar ROI"},
        relacionados=["visor_controles", "metricas", "exportar"],
    ),
    Tema(
        id="metricas", titulo="Qué son Dice e IoU", sugerencia="¿Qué significan Dice e IoU?",
        frases=[("que significan dice e iou", 1.5), "que es el dice", "que es dice", "que es iou",
                "dice", "iou", "indice de dice", "jaccard", "metricas del resultado", "que son las metricas",
                "que miden las metricas", "como se calcula el dice", "interseccion sobre union",
                "coeficiente de similitud", "que significa dice", "que mide el dice", "metrica",
                "rango del dice", "valores del dice", "de 0 a 1", "para que sirven dice e iou"],
        intro="Dice e IoU son dos medidas de coincidencia entre la ROI del modelo y la máscara de referencia:",
        pasos=[
            "Van de 0 (sin coincidencia) a 1 (coincidencia total).",
            "Se muestran en «Métricas del resultado», en «Visualizar ROI», y el Dice también en «Mis estudios».",
            "Solo se calculan si cargaste una máscara de referencia; si no, aparece «No disponible».",
        ],
        nota="Miden cuánto se parecen dos máscaras, no el estado de salud de nadie. "
             "Dependen de la calidad de la referencia.",
        enlace={"ruta": "/roi", "texto": "Ir a Visualizar ROI"},
        relacionados=["interpretar_dice", "mascara_que_es", "comparar_roi"],
    ),
    Tema(
        id="interpretar_dice", titulo="Cómo leer un valor de Dice",
        sugerencia="¿Qué significa un Dice de 0.85?",
        frases=[("que significa un dice de 0 85", 1.5), "dice de 0 85", "dice alto", "dice bajo",
                "dice cercano a 1", "dice cercano a 0", "es bueno un dice", "dice de 0 9",
                "como leo el dice", "como interpreto el dice", "como leer una metrica",
                "como interpreto las metricas", "valor del dice", "que valor es bueno", "que es un buen dice",
                "dice mayor es mejor", "dice 0 5", "dice 0 7", "iou 0 7", "como interpreto dice e iou",
                "un dice de", "mi dice es", "interpretar las metricas"],
        intro="Dice e IoU se leen como grado de coincidencia con la máscara de referencia:",
        pasos=[
            "Un valor como 0.85 significa que la ROI del modelo y la referencia coinciden en gran parte "
            "(85 % de acuerdo en el sentido de la métrica Dice).",
            "Cuanto más cerca de 1, mayor coincidencia; cuanto más cerca de 0, menor.",
            "El IoU suele ser algo menor que el Dice para el mismo par de máscaras; es normal.",
            "El valor depende de la calidad de la referencia y de la imagen.",
        ],
        nota="Es acuerdo entre dos máscaras, no una medida de salud ni de riesgo. Mi ayuda se limita al uso de la app.",
        relacionados=["metricas", "mascara_que_es", "limitaciones"],
    ),
    Tema(
        id="exportar", titulo="Exportar una imagen", sugerencia="¿Cómo exporto la imagen con la ROI?",
        frases=[("como exporto la imagen", 1.5), "exportar imagen", "exportar png", "descargar la imagen",
                "guardar la imagen", "descargar png", "guardar el resultado", "como descargo el resultado",
                "exportar el resultado", "boton exportar imagen", "bajar la imagen", "imprimir resultado",
                "sacar captura", "descargar resultado", "exportar la roi", "guardar la roi",
                "descargar la roi"],
        intro="Puedes exportar el resultado como imagen PNG desde «Visualizar ROI»:",
        pasos=[
            "Abre el estudio procesado en «Visualizar ROI».",
            "Baja a la tarjeta «Métricas del resultado» y pulsa «Exportar imagen».",
            "Se descarga un archivo PNG llamado roi-EST-XXXX.png con el corte central, la ROI superpuesta y el "
            "aviso de resultado experimental impreso.",
        ],
        nota="La exportación siempre es del corte central, sin importar el corte que estés viendo.",
        enlace={"ruta": "/roi", "texto": "Ir a Visualizar ROI"},
        relacionados=["comparar_roi", "limitaciones", "visor_controles"],
    ),
    # ---------------------------------------------------------------- historial
    Tema(
        id="mis_estudios", titulo="Mis estudios e historial",
        sugerencia="¿Qué veo en Mis estudios?",
        frases=[("mis estudios", 1.5), "historial", "historial de estudios", "lista de estudios",
                "estudios cargados", "ver mis estudios", "mis cargas", "buscar un estudio",
                "filtrar estudios", "filtrar por estado", "estados de los estudios", "que significa el estado",
                "listo para procesar", "completado", "pendiente", "id anonimo", "codigo del estudio",
                "tabla de estudios", "estudios anteriores", "donde estan mis estudios", "que estados hay",
                "fecha de carga"],
        intro="«Mis estudios» es tu historial:",
        pasos=[
            "Una tabla con ID anónimo, formato, fecha de carga, estado, Dice y la acción disponible.",
            "Las pestañas (Todos, Completados, Listos para procesar, No compatibles), el buscador por ID y los "
            "filtros de estado y fecha te ayudan a encontrar un estudio.",
            "Los estados posibles son: listo para procesar, pendiente, en proceso, completado, fallido y no compatible.",
            "Desde la acción de cada fila abres «Ver ROI» (si está completado) o «Procesar / Ver detalles».",
        ],
        nota="Solo ves tus propios estudios.",
        enlace={"ruta": "/estudios", "texto": "Ir a Mis estudios"},
        relacionados=["eliminar", "procesar", "ver_resultados"],
    ),
    Tema(
        id="eliminar", titulo="Eliminar un estudio", sugerencia="¿Cómo elimino un estudio?",
        frases=[("como elimino un estudio", 1.5), "borrar un estudio", "eliminar estudio", "quitar un estudio",
                "borrar mis datos", "eliminar mis archivos", "como borro un estudio", "eliminar un resultado",
                "suprimir estudio", "borrar archivos", "papelera", "se pueden recuperar", "deshacer eliminacion",
                "eliminar todo", "no puedo eliminar un estudio", "eliminar estudio en proceso"],
        intro="Para eliminar un estudio:",
        pasos=[
            "Ve a «Mis estudios» y busca la fila del estudio.",
            "Pulsa el icono de papelera (Eliminar EST-XXXX).",
            "Confirma con «Sí, eliminar» en el cuadro de diálogo.",
        ],
        nota="Se borran sus archivos y resultados, y no se puede deshacer. No se puede eliminar un estudio "
             "mientras está pendiente o en proceso.",
        enlace={"ruta": "/estudios", "texto": "Ir a Mis estudios"},
        relacionados=["mis_estudios", "privacidad", "cargar"],
    ),
    # ---------------------------------------------------------------- privacidad y modelo
    Tema(
        id="privacidad", titulo="Privacidad y desidentificación",
        sugerencia="¿Qué pasa con mis datos y mi privacidad?",
        frases=[("privacidad", 1.2), "datos personales", "mis datos", "que datos guarda la aplicacion",
                "desidentificacion", "desidentificar", "anonimo", "anonimizacion", "metadatos dicom",
                "es seguro", "seguridad de mis datos", "donde se guardan los archivos",
                "nombres en los archivos", "puedo subir datos de pacientes", "datos de pacientes",
                "pacientes reales", "informacion personal", "proteccion de datos", "confidencialidad",
                "se guardan mis imagenes", "imagenes reales", "datos reales", "se puede usar con imagenes reales",
                "puedo usar imagenes reales", "personas reales", "quien ve mis estudios", "cumple la ley de datos", "habeas data"],
        intro="Prosta-AI está pensada para trabajar solo con datos públicos y desidentificados:",
        pasos=[
            "No subas datos de personas reales ni incluyas nombres en los archivos.",
            "Solo se guardan tu usuario, un hash de tu contraseña, un ID anónimo por estudio y los archivos "
            "de imagen con nombres neutros.",
            "En DICOM se eliminan los datos de persona, institución, fechas y etiquetas privadas antes de leerlo; "
            "si no es posible, el estudio se rechaza y sus archivos se borran.",
            "Ves solo tus estudios y puedes eliminarlos en cualquier momento desde «Mis estudios».",
        ],
        nota="Usa únicamente archivos de prueba sin datos personales.",
        enlace={"ruta": "/estudios", "texto": "Ir a Mis estudios"},
        relacionados=["datos_prueba", "eliminar", "limitaciones"],
    ),
    Tema(
        id="modelo", titulo="El modelo de segmentación",
        sugerencia="¿Qué modelo usa la aplicación?",
        frases=[("que modelo usan", 1.5), "que modelo usa la aplicacion", "el modelo es bueno",
                "que tan bueno es el modelo", "es confiable el modelo", "que tan preciso es el modelo",
                "precision del modelo", "que algoritmo usan", "red neuronal", "u net", "unet", "monai",
                "prostate mri anatomy", "prostate158", "con que se entreno el modelo",
                "entrenamiento del modelo", "inteligencia artificial", "cuan preciso es", "evaluacion del modelo",
                "dice medio del modelo", "el modelo funciona bien", "que tan confiable es",
                "modelo preentrenado", "que version del modelo", "metricas del modelo", "que ia usan",
                "es bueno el modelo", "rendimiento del modelo"],
        intro="El modelo es una U-Net del MONAI Model Zoo llamada «prostate_mri_anatomy» (licencia Apache 2.0):",
        pasos=[
            "Viene preentrenado con el conjunto público Prostate158 (imágenes T2).",
            "En la evaluación del proyecto sobre el conjunto de prueba de MSD Task05 obtuvo un Dice medio de "
            "0,89 (informes en reports/evaluacion/).",
            "Ese resultado puede estar sobreestimado: no se puede garantizar que los datos de Task05 estén "
            "ausentes del preentrenamiento del modelo.",
            "El nombre y la versión del modelo aparecen bajo «Métricas del resultado» en «Visualizar ROI».",
        ],
        nota="Es un modelo experimental con fines académicos, no validado clínicamente. "
             "Mi ayuda se limita al uso de la app.",
        enlace={"ruta": "/roi", "texto": "Ir a Visualizar ROI"},
        relacionados=["limitaciones", "metricas", "segmentacion"],
    ),
    Tema(
        id="resonancia", titulo="Qué es una resonancia magnética",
        sugerencia="¿Qué es una resonancia magnética?",
        frases=[("que es una resonancia", 1.5), "que es la resonancia magnetica", "que es una mri",
                "que es mri", "que es una rm", "que es t2", "que imagen usa la app", "que tipo de imagen"],
        intro="En términos generales y sin interpretación clínica:",
        pasos=[
            "La resonancia magnética (MRI) es una técnica que genera imágenes del interior del cuerpo "
            "como una pila de cortes.",
            "Prosta-AI trabaja con la secuencia T2 de estudios públicos de próstata, en formato DICOM o NIfTI.",
            "En «Visualizar ROI» puedes recorrer esos cortes uno a uno con el control «Corte».",
        ],
        nota="Para el significado médico de una resonancia, consulta a un profesional de la salud. "
             "Mi ayuda se limita al uso de la app.",
        enlace={"ruta": "/roi", "texto": "Ir a Visualizar ROI"},
        relacionados=["segmentacion", "formatos", "datos_prueba"],
    ),
    Tema(
        id="segmentacion", titulo="Qué es la segmentación y la ROI",
        sugerencia="¿Qué es la segmentación?",
        frases=[("que es la segmentacion", 1.5), "que es la roi", "que es una roi", "que significa roi",
                "region de interes", "que es segmentar", "que significa segmentacion",
                "que es la mascara", "que es el contorno", "que es la segmentacion de imagenes",
                "que es una segmentacion", "definicion de roi", "que es el contorno teal",
                "que significa segmentar", "que muestra la roi", "que es la prostata en la imagen",
                "que segmenta el modelo", "que delimita el modelo", "que representa la roi"],
        intro="Dicho en simple y sin interpretación clínica:",
        pasos=[
            "Segmentar es delimitar en la imagen una zona concreta, corte por corte.",
            "Aquí el modelo experimental propone qué zona corresponde a la próstata; esa propuesta es la ROI "
            "(región de interés).",
            "La ROI se muestra como un contorno de color sobre la imagen y puedes ocultarla o ajustar su opacidad.",
        ],
        nota=NOTA_ROI,
        enlace={"ruta": "/roi", "texto": "Ir a Visualizar ROI"},
        relacionados=["comparar_roi", "limitaciones", "modelo"],
    ),
    Tema(
        id="limitaciones", titulo="Limitaciones de la aplicación",
        sugerencia="¿Cuáles son las limitaciones de la ROI?",
        frases=[("limitaciones", 1.5), "limitaciones de la roi", "cuales son los limites", "que no puede hacer",
                "es experimental", "resultado experimental", "es preciso", "puede tener errores",
                "la roi es exacta", "sustituye a un profesional", "uso clinico", "es un dispositivo medico",
                "se puede usar en un hospital", "es fiable", "es confiable", "que tan confiable es la app",
                "aviso experimental", "para que no sirve", "alcance de la aplicacion", "advertencia",
                "puedo confiar en la roi", "la roi es perfecta", "uso academico", "esta validada",
                "tiene validez clinica"],
        intro="Prosta-AI es un laboratorio académico y experimental. Ten presente:",
        pasos=[
            "La ROI puede ser imprecisa y no implica un hallazgo.",
            "Dice e IoU dependen de la calidad de la máscara de referencia y solo miden coincidencia entre máscaras.",
            "Es solo para archivos de prueba públicos; no es un dispositivo médico ni tiene uso clínico.",
            "No emite diagnósticos ni sustituye la valoración de un profesional de la salud.",
        ],
        nota="Todas las pantallas con resultados muestran el aviso de resultado experimental.",
        relacionados=["modelo", "metricas", "privacidad"],
    ),
    Tema(
        id="asistente", titulo="Qué puede hacer el asistente",
        sugerencia="¿En qué me puedes ayudar?",
        frases=[("en que me puedes ayudar", 1.5), "que puedes hacer", "que sabes hacer", "que haces",
                "ayuda", "necesito ayuda", "como funciona el asistente", "que puedo preguntarte",
                "que temas conoces", "quien eres", "eres una ia", "eres un robot", "sobre que puedo preguntar",
                "para que sirves", "como me ayudas", "que me puedes decir", "que preguntas respondes",
                "puedes ayudarme", "ayudame", "ayuda con la app", "que es el asistente",
                "como usar el asistente", "ayudame con la aplicacion", ("que es el asistente ia", 1.5),
                ("asistente ia", 1.5)],
        intro="Soy un asistente de uso: te explico cómo usar Prosta-AI. Mis respuestas son fijas y revisadas, "
              "no se generan al momento. Puedo orientarte sobre:",
        pasos=[
            "Carga y validación de archivos: formatos, tamaño, máscara de referencia y datos de prueba.",
            "Navegación por el flujo: procesar, etapas, tiempos y qué hacer si algo falla.",
            "Controles del comparador: corte, opacidad, zoom, Dice e IoU y exportación.",
            "Limitaciones de la ROI, privacidad y el modelo.",
            "Tus propios estudios: por ejemplo, el estado de tu último estudio o por qué falló.",
        ],
        nota="No interpreto imágenes ni resultados clínicos, no diagnostico ni tomo decisiones por ti.",
        relacionados=["flujo", "primeros_pasos", "limitaciones"],
    ),
]

POR_ID: dict[str, Tema] = {t.id: t for t in TEMAS}

# Preguntas de arranque cuando no hay temas cercanos
SUGERENCIAS_BASE = [
    POR_ID["primeros_pasos"].sugerencia,
    POR_ID["formatos"].sugerencia,
    POR_ID["comparar_roi"].sugerencia,
]
