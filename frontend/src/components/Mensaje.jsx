import { AlertCircle, CheckCircle2, Info } from 'lucide-react';

const ICONOS = { error: AlertCircle, ok: CheckCircle2, info: Info };

// Mensaje de error o éxito accesible
export default function Mensaje({ tipo = 'error', children }) {
  if (!children) return null;
  const Icono = ICONOS[tipo];
  return (
    <div className={`mensaje mensaje-${tipo}`} role={tipo === 'error' ? 'alert' : 'status'}>
      <Icono size={18} aria-hidden="true" />
      <div>{children}</div>
    </div>
  );
}
