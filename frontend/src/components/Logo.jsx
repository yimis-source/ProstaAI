import { Scan } from 'lucide-react';

// Marca de Prosta-AI
export default function Logo({ claro = false }) {
  return (
    <div className={`logo ${claro ? 'logo-claro' : ''}`}>
      <span className="logo-icono"><Scan size={20} strokeWidth={2} aria-hidden="true" /></span>
      <span className="logo-texto">Prosta-AI</span>
    </div>
  );
}
