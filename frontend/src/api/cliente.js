// Cliente HTTP base: añade el token, interpreta errores y maneja el 401.
const BASE = (import.meta.env.VITE_API_URL || '') + '/api';
const CLAVE_TOKEN = 'prosta_token';
const CLAVE_ALIAS = 'prosta_alias';

export const sesion = {
  token: () => sessionStorage.getItem(CLAVE_TOKEN),
  alias: () => sessionStorage.getItem(CLAVE_ALIAS),
  guardar(token, alias) {
    sessionStorage.setItem(CLAVE_TOKEN, token);
    sessionStorage.setItem(CLAVE_ALIAS, alias);
  },
  borrar() {
    sessionStorage.removeItem(CLAVE_TOKEN);
    sessionStorage.removeItem(CLAVE_ALIAS);
  },
};

// Función que se ejecuta cuando el servidor responde 401 (la define AuthContext)
let alExpirar = () => {};
export const registrarAlExpirar = (fn) => {
  alExpirar = fn;
};

// Extrae el mensaje del campo `detail` (texto o lista de validación)
function mensajeDe(datos, estado) {
  const d = datos && datos.detail;
  if (typeof d === 'string') return d;
  if (Array.isArray(d) && d.length) return d.map((x) => x.msg || String(x)).join('. ');
  return `No se pudo completar la solicitud (código ${estado}).`;
}

export class ErrorApi extends Error {
  constructor(mensaje, estado) {
    super(mensaje);
    this.estado = estado;
  }
}

async function peticion(ruta, { metodo = 'GET', json, formData, tipo = 'json', conToken = true } = {}) {
  const cabeceras = {};
  const token = sesion.token();
  if (conToken && token) cabeceras.Authorization = `Bearer ${token}`;
  let cuerpo;
  if (json !== undefined) {
    cabeceras['Content-Type'] = 'application/json';
    cuerpo = JSON.stringify(json);
  } else if (formData) {
    cuerpo = formData;
  }

  let resp;
  try {
    resp = await fetch(BASE + ruta, { method: metodo, headers: cabeceras, body: cuerpo });
  } catch {
    throw new ErrorApi('No se pudo conectar con el servidor. Revise que esté en ejecución.', 0);
  }

  if (!resp.ok) {
    let datos = null;
    try {
      datos = await resp.json();
    } catch {
      /* respuesta sin cuerpo JSON */
    }
    // Un 401 con sesión iniciada significa token vencido; en el acceso es contraseña incorrecta
    if (resp.status === 401 && token) alExpirar();
    throw new ErrorApi(mensajeDe(datos, resp.status), resp.status);
  }
  if (resp.status === 204) return null;
  return tipo === 'blob' ? resp.blob() : resp.json();
}

export default peticion;
