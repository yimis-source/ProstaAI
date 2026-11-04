// Texto fijo del aviso (igual al del backend)
export const AVISO_EXPERIMENTAL =
  'Resultado experimental con fines académicos. No es un diagnóstico ni sustituye la valoración de un profesional de la salud.';

export const ETAPAS = ['control de calidad', 'preparación', 'segmentación', 'ROI', 'evaluación'];

// Formatea una fecha ISO para mostrarla
export const formatearFecha = (iso) =>
  iso ? new Date(iso).toLocaleString('es', { dateStyle: 'medium', timeStyle: 'short' }) : '—';

export const formatearTamano = (bytes) => {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
};

export const formatearSegundos = (s) =>
  s === null || s === undefined ? '—' : `${Number(s).toFixed(1)} s`;

export const formatearMetrica = (v) =>
  v === null || v === undefined ? null : Number(v).toFixed(3);

export const SIN_REFERENCIA = 'No disponible: el estudio no tiene máscara de referencia';

// Mayúscula inicial para mostrar estados
export const capitalizar = (t) => (t ? t.charAt(0).toUpperCase() + t.slice(1) : t);

// "1 min 42 s" a partir de segundos
export function formatearDuracion(s) {
  if (s === null || s === undefined || Number.isNaN(s)) return '—';
  const total = Math.max(0, Math.round(s));
  const m = Math.floor(total / 60);
  return m ? `${m} min ${total % 60} s` : `${total} s`;
}

// Fecha corta tipo "23 oct 2026 · 09:42"
export function formatearFechaCorta(iso) {
  if (!iso) return '—';
  const d = new Date(iso);
  const f = d.toLocaleDateString('es', { day: 'numeric', month: 'short', year: 'numeric' }).replace(/\./g, '');
  const h = d.toLocaleTimeString('es', { hour: '2-digit', minute: '2-digit', hour12: false });
  return `${f} · ${h}`;
}
