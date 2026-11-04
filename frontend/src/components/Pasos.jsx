import { Check } from 'lucide-react';

const PASOS = ['Cargar', 'Procesar', 'Visualizar'];

// Indicador de pasos Cargar -> Procesar -> Visualizar (actual: 1, 2 o 3)
export default function Pasos({ actual }) {
  return (
    <ol className="pasos" aria-label="Pasos del flujo">
      {PASOS.map((nombre, i) => {
        const n = i + 1;
        const estado = n < actual ? 'hecho' : n === actual ? 'actual' : 'pendiente';
        return (
          <li key={nombre} className={`paso paso-${estado}`} aria-current={estado === 'actual' ? 'step' : undefined}>
            <span className="paso-num">{estado === 'hecho' ? <Check size={14} aria-hidden="true" /> : n}</span>
            <span className="paso-nombre">{nombre}</span>
            <span className="paso-linea" aria-hidden="true" />
          </li>
        );
      })}
    </ol>
  );
}
