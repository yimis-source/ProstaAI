import { Check, CircleDashed, Loader, X } from 'lucide-react';
import { ETAPAS, capitalizar, formatearSegundos } from '../constantes.js';

const DESCRIPCIONES = {
  'control de calidad': 'Formato y estructura de los archivos verificados.',
  preparación: 'Series organizadas y volumen preparado.',
  segmentación: 'Ejecución del modelo experimental.',
  ROI: 'Región de interés disponible en el comparador.',
  evaluación: 'Comparación con la referencia, si existe.',
};
const ICONOS = { pendiente: CircleDashed, 'en proceso': Loader, completado: Check, fallido: X };

// Lista de las 5 etapas con estado, icono y duración
export default function Etapas({ etapas = [] }) {
  const porNombre = Object.fromEntries(etapas.map((e) => [e.nombre, e]));
  return (
    <ol className="etapas">
      {ETAPAS.map((nombre) => {
        const e = porNombre[nombre] || { estado: 'pendiente', duracion_s: null };
        const Icono = ICONOS[e.estado];
        return (
          <li key={nombre} className={`etapa etapa-${e.estado.replace(' ', '-')}`}>
            <span className="etapa-icono"><Icono size={18} aria-hidden="true" /></span>
            <div className="etapa-info">
              <span className="etapa-nombre">{capitalizar(nombre)}</span>
              <span className="etapa-desc">{DESCRIPCIONES[nombre]}</span>
            </div>
            <div className="etapa-lado">
              <span className="etapa-tiempo">{formatearSegundos(e.duracion_s)}</span>
              <span className="etapa-estado">{capitalizar(e.estado)}</span>
            </div>
          </li>
        );
      })}
    </ol>
  );
}
