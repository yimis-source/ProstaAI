"""Casos definidos del asistente de uso (CU06): temas esperados, filtro clínico y contexto."""

import pytest

from prosta_ai.assistant import ContextoUsuario, responder
from prosta_ai.assistant.conocimiento import POR_ID, RUTAS_VALIDAS, TEMAS
from prosta_ai.assistant.motor import es_clinica
from prosta_ai.constantes import AVISO_EXPERIMENTAL

# (pregunta, tema esperado)
CASOS_DE_USO = [
    # las 22 preguntas de la sonda inicial
    ("que es prosta ai", "que_es"),
    ("como funciona", "flujo"),
    ("que hago primero", "primeros_pasos"),
    ("por que fallo mi estudio", "error_proceso"),
    ("donde veo los resultados", "ver_resultados"),
    ("el modelo es bueno?", "modelo"),
    ("que modelo usan", "modelo"),
    ("que es la segmentacion", "segmentacion"),
    ("no me deja procesar", "error_proceso"),
    ("que es una resonancia", "resonancia"),
    ("que es una resonancia magnetica?", "resonancia"),
    ("de donde saco imagenes de prueba", "datos_prueba"),
    ("gracias", "gracias"),
    ("que formatos puedo cargar?", "formatos"),
    ("como cambio de corte o ajusto la opacidad?", "visor_controles"),
    ("que pasa si no tengo mascara de referencia", "mascara_sin"),
    ("me salio un error", "error_proceso"),
    ("hola", "saludo"),
    ("como cargo un estudio", "cargar"),
    ("que significa dice", "metricas"),
    ("como exporto la imagen", "exportar"),
    ("como elimino un estudio", "eliminar"),
    ("cuanto tarda el procesamiento", "tiempos"),
    # con signos, tildes y mayúsculas
    ("¿Qué es Prosta-AI?", "que_es"),
    ("¿Cómo comparo la ROI con la imagen original?", "comparar_roi"),
    ("¿Qué significa cada etapa del procesamiento?", "etapas"),
    ("¿Qué significa Dice e IoU?", "metricas"),
    ("¿Qué es la máscara de referencia?", "mascara_que_es"),
    ("¿Cómo subo la máscara de referencia?", "mascara_subir"),
    ("¿Cómo cierro sesión?", "cerrar_sesion"),
    ("¿Qué veo en Mis estudios?", "mis_estudios"),
    ("¿Qué secciones tiene el menú?", "menu"),
    ("¿Qué pasa con mis datos y mi privacidad?", "privacidad"),
    # sin tildes, con errores de escritura y mayúsculas
    ("QUE FORMATOS ACEPTA", "formatos"),
    ("COMO SUBO UN ARCHIVO", "cargar"),
    ("cargarr estudio", "cargar"),
    ("como porcesar un estudio", "procesar"),
    ("formatoss admitidos", "formatos"),
    ("COMO EXPORTO EL PNG", "exportar"),
    ("cuanto tarda", "tiempos"),
    ("es muy lento el procesamiento", "tiempos"),
    ("buenas tardes", "saludo"),
    ("muchas gracias!", "gracias"),
    ("adios", "despedida"),
    ("hasta luego", "despedida"),
    # flujo y primeros pasos
    ("por donde empiezo", "primeros_pasos"),
    ("no se por donde empezar", "primeros_pasos"),
    ("explicame como funciona la aplicacion", "flujo"),
    ("para que sirve esta app", "que_es"),
    ("en que me puedes ayudar", "asistente"),
    ("que puedes hacer", "asistente"),
    # acceso
    ("como inicio sesion por primera vez", "acceso"),
    ("olvide mi contraseña", "acceso"),
    ("como salgo de la aplicacion", "cerrar_sesion"),
    # carga, formatos, rechazo
    ("puedo subir un zip con dicom", "formatos"),
    ("cual es el tamaño maximo de archivo", "formatos"),
    ("acepta nifti", "formatos"),
    ("como subo mi resonancia", "cargar"),
    ("puedo usar dicom", "formatos"),
    ("se puede usar con imagenes reales", "privacidad"),
    ("que es el asistente ia", "asistente"),
    ("por que se rechaza mi estudio", "rechazo_carga"),
    ("mi estudio aparece como no compatible", "rechazo_carga"),
    ("donde subo los archivos", "cargar"),
    # máscara
    ("necesito la mascara de referencia", "mascara_que_es"),
    ("no tengo mascara", "mascara_sin"),
    ("por que no aparece el dice", "mascara_sin"),
    ("como agrego la referencia", "mascara_subir"),
    # datos de prueba
    ("donde descargo estudios de ejemplo", "datos_prueba"),
    ("que es task05", "datos_prueba"),
    ("no tengo imagenes para probar", "datos_prueba"),
    # procesamiento
    ("que etapas hay", "etapas"),
    ("para que sirve el control de calidad", "etapas"),
    ("como inicio el procesamiento", "procesar"),
    ("donde esta el boton procesar", "procesar"),
    ("el procesamiento fallo", "error_proceso"),
    ("que hago si falla la segmentacion", "error_proceso"),
    ("como reintento", "error_proceso"),
    # resultados y visor
    ("como veo la roi", "ver_resultados"),
    ("como hago zoom", "visor_controles"),
    ("como oculto la roi", "visor_controles"),
    ("con las flechas del teclado cambio de corte", "visor_controles"),
    ("que muestra cada panel", "comparar_roi"),
    ("para que sirven los dos paneles", "comparar_roi"),
    ("que mide el dice", "metricas"),
    ("que es el iou", "metricas"),
    ("que significa un dice de 0.85", "interpretar_dice"),
    ("un dice alto es mejor", "interpretar_dice"),
    ("como interpreto el dice", "interpretar_dice"),
    ("como descargo el resultado", "exportar"),
    ("exportar png", "exportar"),
    # historial
    ("donde estan mis estudios", "mis_estudios"),
    ("que estados puede tener un estudio", "mis_estudios"),
    ("como borro un estudio", "eliminar"),
    ("se pueden recuperar los estudios eliminados", "eliminar"),
    # privacidad, modelo, conceptos, límites
    ("puedo subir datos de pacientes", "privacidad"),
    ("se guardan mis imagenes", "privacidad"),
    ("que algoritmo usan", "modelo"),
    ("con que se entreno el modelo", "modelo"),
    ("que tan preciso es el modelo", "modelo"),
    ("que es la roi", "segmentacion"),
    ("que significa roi", "segmentacion"),
    ("cuales son las limitaciones", "limitaciones"),
    ("es un dispositivo medico", "limitaciones"),
    ("puedo confiar en la roi", "limitaciones"),
]

CLINICAS = [
    "esta bien mi prostata", "puedo usarlo para mi papa", "¿Tengo cáncer?", "Qué tratamiento me recomiendan",
    "Esto es un diagnóstico?", "Tengo síntomas", "dice que el tumor es benigno", "estoy enfermo",
    "es grave", "que tan malo es", "debo preocuparme", "mi resultado es normal?", "interpreta mi resonancia",
    "me duele la prostata", "que significa mi resonancia", "tengo psa alto", "necesito una biopsia?",
    "que medicamento tomo", "mi abuelo tiene la prostata grande", "me tengo que operar?",
    "hay algo malo en la imagen", "puedo saber si tengo cancer con esto", "es normal mi prostata",
    "cuanto tiempo de vida me queda", "voy a morir", "mi papa esta enfermo, sirve la app?",
    "me recomiendan cirugia", "es maligno o benigno", "el resultado es positivo", "esto indica un tumor",
    "puedo ver si estoy sano", "que dosis me toca", "le doy esta imagen a mi medico?",
    "que pronostico tengo", "mi prostata se ve mal",
]

NO_CLINICAS = [
    "que significa un dice de 0.85", "que es la segmentacion", "que es la roi", "el modelo es bueno?",
    "puedo subir datos de pacientes", "la roi se superpone sobre la prostata en cada corte",
    "con que imagenes de resonancia magnetica se entreno el modelo", "que es una resonancia magnetica",
    "es normal que el procesamiento tarde", "como interpreto la roi en el comparador",
    "un dice alto es un buen resultado", "puedo cargar una resonancia de prostata en formato dicom",
    "el estudio salio mal, que hago", "el dice sale 0.3, es malo?", "que segmenta el modelo en la prostata",
]


@pytest.mark.parametrize("pregunta,esperado", CASOS_DE_USO)
def test_tema_esperado(pregunta, esperado):
    r = responder(pregunta)
    assert r["tema"] == esperado, (pregunta, r["tema"])


@pytest.mark.parametrize("pregunta", CLINICAS)
def test_preguntas_clinicas_se_rechazan(pregunta):
    r = responder(pregunta)
    assert r["tema"] == "clinico", pregunta
    assert "profesional de la salud" in r["respuesta"]
    assert r["pasos"] == [] and r["enlace"] is None
    assert len(r["sugerencias"]) == 3 and r["aviso"] == AVISO_EXPERIMENTAL


@pytest.mark.parametrize("pregunta", NO_CLINICAS)
def test_preguntas_de_uso_con_palabras_medicas_no_se_bloquean(pregunta):
    assert not es_clinica(pregunta), pregunta
    assert responder(pregunta)["tema"] != "clinico"


def test_filtro_clinico_gana_aunque_haya_contexto_de_uso():
    r = responder("como cargo mi estudio para saber si tengo cancer")
    assert r["tema"] == "clinico"


@pytest.mark.parametrize("pregunta", [
    "xyz qwerty", "banana", "cual es la capital de francia", "cuentame un chiste", "asdf jkl",
])
def test_no_entendido_ofrece_tres_sugerencias(pregunta):
    r = responder(pregunta)
    assert r["tema"] == "no_entendido"
    assert len(r["sugerencias"]) == 3
    assert "Intente reformular su pregunta" not in r["respuesta"]
    assert all(s in r["respuesta"] for s in r["sugerencias"])


def test_contrato_de_respuesta():
    r = responder("como comparo la roi con la imagen original")
    assert set(r) == {"tema", "respuesta", "intro", "pasos", "nota", "enlace", "sugerencias", "aviso"}
    assert r["intro"] in r["respuesta"] and r["nota"] in r["respuesta"]
    assert all(f"{i}. {p}" in r["respuesta"] for i, p in enumerate(r["pasos"], 1))
    assert r["enlace"] == {"ruta": "/roi", "texto": "Ir a Visualizar ROI"}
    assert 1 <= len(r["sugerencias"]) <= 3
    assert r["aviso"] == AVISO_EXPERIMENTAL


def test_respuesta_del_diseno_para_comparar_roi():
    r = responder("¿Cómo comparo la ROI con la imagen original?")
    assert r["intro"] == "En «Visualizar ROI» encontrarás dos paneles con el mismo corte de prueba:"
    assert r["pasos"][0] == "Original muestra la imagen sin superposición."
    assert "no implica un hallazgo" in r["nota"]


def test_es_determinista():
    assert responder("que formatos puedo cargar") == responder("que formatos puedo cargar")


# ------------------------------------------------------------------ base de conocimiento
def test_base_de_conocimiento_es_consistente():
    ids = [t.id for t in TEMAS]
    assert len(ids) == len(set(ids)) and len(TEMAS) >= 30
    for t in TEMAS:
        assert t.enlace is None or t.enlace["ruta"] in RUTAS_VALIDAS, t.id
        assert t.enlace is None or t.enlace["texto"], t.id
        assert all(r in POR_ID for r in t.relacionados), t.id
        assert t.id not in t.relacionados and 1 <= len(t.relacionados) <= 3, t.id
        assert t.intro and t.frases and t.sugerencia, t.id


@pytest.mark.parametrize("tema", TEMAS, ids=lambda t: t.id)
def test_cada_sugerencia_lleva_a_su_tema(tema):
    assert responder(tema.sugerencia)["tema"] == tema.id


@pytest.mark.parametrize("tema", TEMAS, ids=lambda t: t.id)
def test_las_frases_de_los_temas_no_activan_el_filtro_clinico(tema):
    for f in tema.frases:
        texto = f[0] if isinstance(f, tuple) else f
        assert not es_clinica(texto), texto


def test_textos_no_prometen_controles_inexistentes():
    todo = " ".join(t.intro + " ".join(t.pasos) + (t.nota or "") for t in TEMAS)
    for prohibido in ("rotar", "medir distancia", "ventana y nivel", "brillo", "contraste de la imagen"):
        assert prohibido not in todo.lower()


# ------------------------------------------------------------------ contexto del usuario
def _contexto(entorno, alias):
    from prosta_ai.repositories import UserRepository

    sesion = entorno.app.state.session_factory()
    usuario = UserRepository(sesion).por_alias(alias)
    return sesion, ContextoUsuario(sesion, usuario)


def _preguntar(entorno, cab, pregunta):
    r = entorno.client.post("/api/asistente", json={"pregunta": pregunta}, headers=cab)
    assert r.status_code == 200
    return r.json()


def _estudio_fallido(entorno, cab, etapa="segmentación"):
    from apoyo_api import PipelineFalso

    entorno.pipeline = PipelineFalso(falla_en=etapa)
    e = entorno.cargar(cab).json()
    entorno.procesar(cab, e["id"])
    entorno.worker().process_next()
    return e


def test_contexto_estudio_fallido_menciona_etapa_y_error(entorno):
    cab = entorno.cabeceras()
    e = _estudio_fallido(entorno, cab)
    for pregunta in ("por qué falló mi estudio", "me salió un error en mi estudio", "mi último estudio falló"):
        r = _preguntar(entorno, cab, pregunta)
        assert r["tema"] == "ctx_error", pregunta
        assert e["codigo"] in r["intro"] and "«segmentación»" in r["intro"]
        assert "Volumen no válido para esta etapa." in r["respuesta"]
        assert "Volver a procesar" in r["respuesta"]
        assert r["enlace"]["ruta"] == f"/procesamiento?estudio={e['id']}"


def test_contexto_sin_estudios(entorno):
    cab = entorno.cabeceras("sinestudios")
    for pregunta in ("por qué falló mi estudio", "cuántos estudios tengo", "estado de mi último estudio",
                     "cuál es mi último resultado"):
        r = _preguntar(entorno, cab, pregunta)
        assert r["tema"] in ("ctx_sin_estudios", "ctx_resultado"), pregunta
        assert r["enlace"]["ruta"] in ("/cargar", "/procesamiento")
    assert _preguntar(entorno, cab, "cuántos estudios tengo")["enlace"]["ruta"] == "/cargar"


def test_contexto_aislado_entre_usuarios(entorno):
    ana, luis = entorno.cabeceras("ana"), entorno.cabeceras("luis")
    e = _estudio_fallido(entorno, ana)
    r = _preguntar(entorno, luis, "por qué falló mi estudio")
    assert r["tema"] == "ctx_sin_estudios" and e["codigo"] not in r["respuesta"]
    assert _preguntar(entorno, luis, "cuántos estudios tengo")["tema"] == "ctx_sin_estudios"
    assert "1 estudio" in _preguntar(entorno, ana, "cuántos estudios tengo")["intro"]


def test_contexto_conteo_y_estado(entorno):
    cab = entorno.cabeceras()
    e1 = entorno.cargar(cab).json()
    e2 = entorno.cargar(cab).json()
    r = _preguntar(entorno, cab, "cuántos estudios tengo")
    assert r["tema"] == "ctx_conteo" and "2 estudios" in r["intro"]
    assert "Listo para procesar: 2" in r["pasos"]
    r = _preguntar(entorno, cab, "cuál es el estado de mi último estudio")
    assert r["tema"] == "ctx_estado" and e2["codigo"] in r["intro"] and e1["codigo"] not in r["intro"]
    assert "listo para procesar" in r["intro"] and "Procesar" in r["respuesta"]


def test_contexto_resultado_con_referencia_no_da_significado_clinico(entorno):
    cab = entorno.cabeceras()
    e = entorno.cargar(cab, referencia=True).json()
    entorno.procesar(cab, e["id"])
    entorno.worker().process_next()
    r = _preguntar(entorno, cab, "cuál es mi último resultado")
    assert r["tema"] == "ctx_resultado" and e["codigo"] in r["intro"]
    assert "Dice: 0.876" in r["pasos"] and "IoU: 0.780" in r["pasos"]
    assert "no indican nada sobre la salud" in r["nota"]
    assert r["enlace"]["ruta"].startswith("/roi?trabajo=")
    r = _preguntar(entorno, cab, "estado de mi último estudio")
    assert r["tema"] == "ctx_estado" and "completado" in r["intro"]


def test_sin_contexto_las_mismas_preguntas_dan_respuesta_general():
    assert responder("por qué falló mi estudio")["tema"] == "error_proceso"
    assert responder("cuántos estudios tengo")["tema"] != "ctx_conteo"


def test_contexto_directo_con_sesion(entorno):
    cab = entorno.cabeceras("ana")
    _estudio_fallido(entorno, cab)
    sesion, ctx = _contexto(entorno, "ana")
    with sesion:
        r = responder("por qué falló mi estudio", ctx)
    assert r["tema"] == "ctx_error"
    assert responder("¿tengo cáncer?", ctx)["tema"] == "clinico"
