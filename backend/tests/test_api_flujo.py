import io

import pytest
from PIL import Image
from sqlalchemy import select

from apoyo_api import PipelineFalso, nifti_gz
from prosta_ai.constantes import AVISO_EXPERIMENTAL, MENSAJE_ERROR_GENERICO
from prosta_ai.models import Archivo, Estudio, Resultado, Trabajo
from prosta_ai.pipeline.stages import STAGES


def test_salud_y_rutas_protegidas(entorno):
    c = entorno.client
    assert c.get("/api/salud").json() == {"estado": "ok"}
    for ruta in ("/api/estudios", "/api/trabajos/1", "/api/trabajos/1/resultado"):
        assert c.get(ruta).status_code == 401
    assert c.post("/api/asistente", json={"pregunta": "hola"}).status_code == 401
    assert c.get("/api/estudios", headers={"Authorization": "Bearer falso"}).status_code == 401


def test_acceso(entorno):
    c = entorno.client
    assert c.post("/api/acceso/verificar", json={"alias": "ana"}).json() == {"existe": False}
    assert c.post("/api/acceso/verificar", json={"alias": "a"}).status_code == 422
    # primera vez: exige confirmación y longitud
    assert c.post("/api/acceso", json={"alias": "ana", "contrasena": "clave-segura-1"}).status_code == 422
    r = c.post("/api/acceso", json={"alias": "ana", "contrasena": "corta", "confirmacion": "corta"})
    assert r.status_code == 422 and "detail" in r.json()
    r = c.post("/api/acceso", json={"alias": "ana", "contrasena": "clave-segura-1",
                                    "confirmacion": "clave-segura-1"})
    assert r.status_code == 200 and r.json()["primer_acceso"] is True and r.json()["token"]
    assert c.post("/api/acceso/verificar", json={"alias": "ana"}).json() == {"existe": True}
    r = c.post("/api/acceso", json={"alias": "ana", "contrasena": "clave-segura-1"})
    assert r.status_code == 200 and r.json()["primer_acceso"] is False
    assert c.post("/api/acceso", json={"alias": "ana", "contrasena": "equivocada1"}).status_code == 401


def test_flujo_completo(entorno):
    c, cab = entorno.client, entorno.cabeceras()
    r = entorno.cargar(cab, referencia=True)
    assert r.status_code == 201, r.text
    estudio = r.json()
    assert estudio["codigo"] == "EST-0001" and estudio["formato"] == "NIfTI"

    lista = c.get("/api/estudios", headers=cab).json()
    assert lista[0]["estado"] == "listo para procesar"

    r = entorno.procesar(cab, estudio["id"])
    assert r.status_code == 201 and r.json()["estado"] == "pendiente"
    id_trabajo = r.json()["id"]
    assert len(r.json()["etapas"]) == 5

    assert entorno.worker().process_next() is True
    assert entorno.worker().process_next() is False

    t = c.get(f"/api/trabajos/{id_trabajo}", headers=cab).json()
    assert t["estado"] == "completado" and t["etapa_fallida"] is None
    assert [e["nombre"] for e in t["etapas"]] == STAGES
    assert all(e["estado"] == "completado" and e["duracion_s"] == 0.1 for e in t["etapas"])

    res = c.get(f"/api/trabajos/{id_trabajo}/resultado", headers=cab).json()
    assert res["dice"] == pytest.approx(0.876, abs=1e-3) and res["iou"] == pytest.approx(0.78)
    assert res["cortes"] == 12 and res["forma"] == [32, 32, 12]
    assert res["modelo"] == {"nombre": "modelo_prueba", "version": "1"}
    assert res["aviso"] == AVISO_EXPERIMENTAL and res["tiempo_total_s"] >= 0

    # el pipeline recibió la imagen y la referencia por separado
    entrada = entorno.pipeline.entradas[0]
    assert len(entrada.files) == 1 and len(entrada.reference_files) == 1

    img = c.get(f"/api/trabajos/{id_trabajo}/corte/6", headers=cab)
    assert img.headers["content-type"] == "image/png"
    assert Image.open(io.BytesIO(img.content)).mode == "L"
    mask = Image.open(io.BytesIO(c.get(f"/api/trabajos/{id_trabajo}/corte/6?capa=mascara", headers=cab).content))
    assert mask.mode == "RGBA"
    alfas = {a for *_, a in mask.getdata()}
    assert alfas == {0, 114}
    # corte fuera de la esfera: máscara completamente transparente
    vacia = Image.open(io.BytesIO(c.get(f"/api/trabajos/{id_trabajo}/corte/0?capa=mascara", headers=cab).content))
    assert {a for *_, a in vacia.getdata()} == {0}

    assert c.get(f"/api/trabajos/{id_trabajo}/corte/12", headers=cab).status_code == 422
    assert c.get(f"/api/trabajos/{id_trabajo}/corte/-1", headers=cab).status_code == 422
    assert c.get(f"/api/trabajos/{id_trabajo}/corte/1?capa=otra", headers=cab).status_code == 422

    exp = c.get(f"/api/trabajos/{id_trabajo}/exportar", headers=cab)
    assert exp.headers["content-type"] == "image/png"
    exportada = Image.open(io.BytesIO(exp.content))
    assert exportada.height > exportada.width  # incluye el pie con el aviso
    # el pie (franja oscura inferior) contiene texto claro impreso
    pie = exportada.convert("L").crop((0, exportada.height - 40, exportada.width, exportada.height))
    assert max(pie.getdata()) > 200

    lista = c.get("/api/estudios", headers=cab).json()
    assert lista[0]["estado"] == "completado" and lista[0]["id_ultimo_trabajo"] == id_trabajo
    assert lista[0]["dice"] == pytest.approx(0.876, abs=1e-3)
    detalle = c.get(f"/api/estudios/{estudio['id']}", headers=cab).json()
    assert len(detalle["trabajos"]) == 1

    # borrado: filas y archivos
    almacen = entorno.settings.storage_dir
    assert (almacen / "estudios" / "EST-0001").exists()
    assert c.delete(f"/api/estudios/{estudio['id']}", headers=cab).status_code == 204
    assert not (almacen / "estudios" / "EST-0001").exists()
    assert not (almacen / "resultados" / str(id_trabajo)).exists()
    with entorno.app.state.session_factory() as s:
        for modelo in (Estudio, Archivo, Trabajo, Resultado):
            assert s.scalars(select(modelo)).first() is None


def test_resultado_404_si_no_completado(entorno):
    c, cab = entorno.client, entorno.cabeceras()
    e = entorno.cargar(cab).json()
    t = entorno.procesar(cab, e["id"]).json()
    assert c.get(f"/api/trabajos/{t['id']}/resultado", headers=cab).status_code == 404
    assert c.get(f"/api/trabajos/{t['id']}/corte/0", headers=cab).status_code == 404


def test_sin_referencia_metricas_nulas(entorno):
    cab = entorno.cabeceras()
    e = entorno.cargar(cab).json()
    t = entorno.procesar(cab, e["id"]).json()
    entorno.worker().process_next()
    res = entorno.client.get(f"/api/trabajos/{t['id']}/resultado", headers=cab).json()
    assert res["dice"] is None and res["iou"] is None


def test_carga_rechazada(entorno):
    c, cab = entorno.client, entorno.cabeceras()
    r = entorno.cargar(cab, nombre="informe.pdf", contenido=b"%PDF-1.4")
    assert r.status_code == 422 and "Formato no compatible" in r.json()["detail"]
    lista = c.get("/api/estudios", headers=cab).json()
    assert len(lista) == 1 and lista[0]["estado"] == "no compatible"
    with entorno.app.state.session_factory() as s:
        assert s.scalars(select(Archivo)).first() is None
    assert not (entorno.settings.storage_dir / "estudios" / lista[0]["codigo"]).exists()
    # tampoco se puede procesar
    assert entorno.procesar(cab, lista[0]["id"]).status_code == 409
    # tamaño excedido (límite de pruebas: 1 MB)
    r = entorno.cargar(cab, contenido=b"0" * (2 * 1024 * 1024))
    assert r.status_code == 422 and "tamaño" in r.json()["detail"]
    # sin archivos
    assert c.post("/api/estudios", headers=cab).status_code == 422


def test_codigos_secuenciales(entorno):
    cab = entorno.cabeceras()
    codigos = [entorno.cargar(cab).json()["codigo"] for _ in range(3)]
    assert codigos == ["EST-0001", "EST-0002", "EST-0003"]


def test_conflicto_409_y_reintento(entorno):
    c, cab = entorno.client, entorno.cabeceras()
    e = entorno.cargar(cab).json()
    assert entorno.procesar(cab, e["id"]).status_code == 201
    assert entorno.procesar(cab, e["id"]).status_code == 409  # pendiente
    # en proceso
    with entorno.app.state.session_factory() as s:
        t = s.scalars(select(Trabajo)).first()
        t.estado = "en proceso"
        s.commit()
    assert entorno.procesar(cab, e["id"]).status_code == 409
    assert c.delete(f"/api/estudios/{e['id']}", headers=cab).status_code == 409


def test_trabajo_fallido_controlado(entorno):
    c, cab = entorno.client, entorno.cabeceras()
    entorno.pipeline = PipelineFalso(falla_en="segmentación")
    e = entorno.cargar(cab).json()
    id1 = entorno.procesar(cab, e["id"]).json()["id"]
    entorno.worker().process_next()
    t = c.get(f"/api/trabajos/{id1}", headers=cab).json()
    assert t["estado"] == "fallido" and t["etapa_fallida"] == "segmentación"
    assert t["mensaje_error"] == "Volumen no válido para esta etapa."
    estados = {x["nombre"]: x["estado"] for x in t["etapas"]}
    assert estados == {
        "control de calidad": "completado", "preparación": "completado",
        "segmentación": "fallido", "ROI": "pendiente", "evaluación": "pendiente",
    }
    assert c.get(f"/api/trabajos/{id1}/resultado", headers=cab).status_code == 404
    # reintento: nuevo trabajo
    entorno.pipeline = PipelineFalso()
    r = entorno.procesar(cab, e["id"])
    assert r.status_code == 201 and r.json()["id"] != id1
    entorno.worker().process_next()
    assert c.get(f"/api/trabajos/{r.json()['id']}", headers=cab).json()["estado"] == "completado"
    assert len(c.get(f"/api/estudios/{e['id']}", headers=cab).json()["trabajos"]) == 2


def test_error_inesperado_no_expone_detalle(entorno, caplog):
    c, cab = entorno.client, entorno.cabeceras()
    entorno.pipeline = PipelineFalso(explota=True)
    e = entorno.cargar(cab).json()
    id_t = entorno.procesar(cab, e["id"]).json()["id"]
    entorno.worker().process_next()
    t = c.get(f"/api/trabajos/{id_t}", headers=cab).json()
    assert t["estado"] == "fallido" and t["mensaje_error"] == MENSAJE_ERROR_GENERICO
    assert "secreto" not in str(t)
    assert "detalle interno" in caplog.text  # el detalle queda en el log
    assert t["etapa_fallida"] == "preparación"


def test_modelo_no_disponible_falla_en_segmentacion(entorno):
    def sin_modelo():
        raise FileNotFoundError("faltan pesos")

    entorno.app.state.service._provider = sin_modelo
    entorno.app.state.model_info_fn = lambda s: (_ for _ in ()).throw(RuntimeError("sin modelo"))
    entorno.app.state.id_modelo = None
    cab = entorno.cabeceras()
    e = entorno.cargar(cab).json()
    id_t = entorno.procesar(cab, e["id"]).json()["id"]
    entorno.worker().process_next()
    t = entorno.client.get(f"/api/trabajos/{id_t}", headers=cab).json()
    assert t["estado"] == "fallido" and t["etapa_fallida"] == "segmentación"


def test_aislamiento_entre_usuarios(entorno):
    c = entorno.client
    ana, luis = entorno.cabeceras("ana"), entorno.cabeceras("luis", "otra-clave-22")
    e = entorno.cargar(ana).json()
    t = entorno.procesar(ana, e["id"]).json()
    entorno.worker().process_next()
    assert c.get("/api/estudios", headers=luis).json() == []
    for ruta in (f"/api/estudios/{e['id']}", f"/api/trabajos/{t['id']}",
                 f"/api/trabajos/{t['id']}/resultado", f"/api/trabajos/{t['id']}/corte/0",
                 f"/api/trabajos/{t['id']}/exportar"):
        assert c.get(ruta, headers=luis).status_code == 404, ruta
    assert c.delete(f"/api/estudios/{e['id']}", headers=luis).status_code == 404
    assert entorno.procesar(luis, e["id"]).status_code == 404
    assert len(c.get("/api/estudios", headers=ana).json()) == 1


def test_asistente_api(entorno):
    cab = entorno.cabeceras()
    r = entorno.client.post("/api/asistente", json={"pregunta": "¿Qué es Dice?"}, headers=cab)
    assert r.status_code == 200 and r.json()["aviso"] == AVISO_EXPERIMENTAL
    cuerpo = r.json()
    assert cuerpo["tema"] == "metricas" and cuerpo["intro"] in cuerpo["respuesta"]
    assert cuerpo["pasos"] and cuerpo["enlace"]["ruta"] == "/roi" and len(cuerpo["sugerencias"]) == 3
    r = entorno.client.post("/api/asistente", json={"pregunta": "¿Tengo cáncer?"}, headers=cab)
    assert r.json()["tema"] == "clinico" and "profesional" in r.json()["respuesta"]
    r = entorno.client.post("/api/asistente", json={"pregunta": "xyz"}, headers=cab)
    assert r.json()["tema"] == "no_entendido" and len(r.json()["sugerencias"]) == 3
    assert entorno.client.post("/api/asistente", json={"pregunta": ""}, headers=cab).status_code == 422
    assert entorno.client.post("/api/asistente", json={"pregunta": "a" * 501}, headers=cab).status_code == 422


def test_cors(entorno):
    r = entorno.client.options(
        "/api/salud", headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "GET"})
    assert r.headers.get("access-control-allow-origin") == "http://localhost:5173"
