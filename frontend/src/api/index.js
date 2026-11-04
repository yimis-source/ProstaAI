// Funciones de la API (sección 5 de la especificación técnica)
import peticion from './cliente.js';

export const verificarAlias = (alias) =>
  peticion('/acceso/verificar', { metodo: 'POST', json: { alias }, conToken: false });

export const acceder = (alias, contrasena, confirmacion) =>
  peticion('/acceso', {
    metodo: 'POST',
    json: confirmacion === undefined ? { alias, contrasena } : { alias, contrasena, confirmacion },
    conToken: false,
  });

export const listarEstudios = () => peticion('/estudios');
export const obtenerEstudio = (id) => peticion(`/estudios/${id}`);
export const eliminarEstudio = (id) => peticion(`/estudios/${id}`, { metodo: 'DELETE' });

// archivos y referencia son listas de File
export function crearEstudio(archivos, referencia = []) {
  const fd = new FormData();
  archivos.forEach((f) => fd.append('archivos', f));
  referencia.forEach((f) => fd.append('referencia', f));
  return peticion('/estudios', { metodo: 'POST', formData: fd });
}

export const procesarEstudio = (id) => peticion(`/estudios/${id}/procesar`, { metodo: 'POST' });
export const obtenerTrabajo = (id) => peticion(`/trabajos/${id}`);
export const obtenerResultado = (id) => peticion(`/trabajos/${id}/resultado`);

// Los PNG necesitan el token, por eso se piden como blob
export const obtenerCorte = (idTrabajo, indice, capa) =>
  peticion(`/trabajos/${idTrabajo}/corte/${indice}?capa=${capa}`, { tipo: 'blob' });
export const exportarImagen = (idTrabajo) =>
  peticion(`/trabajos/${idTrabajo}/exportar`, { tipo: 'blob' });

export const preguntarAsistente = (pregunta) =>
  peticion('/asistente', { metodo: 'POST', json: { pregunta } });
