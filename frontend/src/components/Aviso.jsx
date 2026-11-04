import { Info } from 'lucide-react';
import { AVISO_EXPERIMENTAL } from '../constantes.js';

// Aviso experimental destacado (franja azul del diseño)
export default function Aviso({ texto = AVISO_EXPERIMENTAL }) {
  return (
    <div className="aviso" role="note">
      <Info size={18} aria-hidden="true" />
      <p>{texto}</p>
    </div>
  );
}
