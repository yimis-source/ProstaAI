import { capitalizar } from '../constantes.js';

// Etiqueta con punto de color según el estado del estudio o del trabajo
const CLASES = {
  completado: 'ok',
  'listo para procesar': 'info',
  pendiente: 'espera',
  'en proceso': 'info',
  fallido: 'error',
  'no compatible': 'espera',
};

export default function EtiquetaEstado({ estado }) {
  return (
    <span className={`etiqueta etiqueta-${CLASES[estado] || 'info'}`}>
      <span className="punto" aria-hidden="true" />
      {capitalizar(estado)}
    </span>
  );
}
