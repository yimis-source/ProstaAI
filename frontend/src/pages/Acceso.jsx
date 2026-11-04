import { useState } from 'react';
import { Navigate, useNavigate } from 'react-router-dom';
import { ArrowRight, Eye, EyeOff, Lock, ShieldCheck, User } from 'lucide-react';
import { acceder, verificarAlias } from '../api/index.js';
import { useAuth } from '../auth/AuthContext.jsx';
import Aviso from '../components/Aviso.jsx';
import Logo from '../components/Logo.jsx';
import Mensaje from '../components/Mensaje.jsx';

// Campo con icono a la izquierda y, si es contraseña, botón para mostrarla
function Campo({ id, etiqueta, icono: Icono, tipo = 'text', valor, onCambio, placeholder, autoComplete, autoFocus, soloLectura }) {
  const [visible, setVisible] = useState(false);
  const esClave = tipo === 'password';
  return (
    <div className="campo">
      <label htmlFor={id}>{etiqueta}</label>
      <div className="campo-caja">
        <Icono size={18} aria-hidden="true" />
        <input id={id} type={esClave && visible ? 'text' : tipo} value={valor} placeholder={placeholder}
          onChange={(e) => onCambio(e.target.value)} autoComplete={autoComplete} autoFocus={autoFocus} readOnly={soloLectura} />
        {esClave && (
          <button type="button" className="campo-ojo" onClick={() => setVisible(!visible)}
            aria-label={visible ? 'Ocultar contraseña' : 'Mostrar contraseña'}>
            {visible ? <EyeOff size={18} aria-hidden="true" /> : <Eye size={18} aria-hidden="true" />}
          </button>
        )}
      </div>
    </div>
  );
}

// Ilustración decorativa del panel izquierdo
function Ilustracion() {
  return (
    <svg viewBox="0 0 600 330" className="ilustracion" aria-hidden="true">
      <line x1="36" y1="165" x2="564" y2="165" stroke="#9DAFDF" strokeOpacity=".4" />
      <line x1="300" y1="30" x2="300" y2="300" stroke="#9DAFDF" strokeOpacity=".4" />
      <circle cx="300" cy="165" r="135" fill="none" stroke="#C7D5FF" strokeOpacity=".7" />
      <circle cx="300" cy="165" r="105" fill="none" stroke="#C7D5FF" strokeOpacity=".7" />
      <path d="M255 150c5-22 25-32 48-30 25 3 45 25 42 52-3 28-30 40-55 37-27-3-43-22-45-40-1-8 2-14 10-19z"
        fill="#47D4BD" fillOpacity=".3" stroke="#66E0CD" strokeWidth="2.5" />
      <rect x="372" y="92" width="82" height="26" rx="5" fill="#1E3A8A" stroke="#66E0CD" />
      <text x="413" y="109" textAnchor="middle" fontSize="11" fontWeight="600" fill="#A8F3E5">ROI / DEMO</text>
    </svg>
  );
}

// Tres pasos: usuario -> contraseña (existente) o primera vez
export default function Acceso() {
  const { alias: sesionAlias, aviso, iniciar } = useAuth();
  const navegar = useNavigate();
  const [paso, setPaso] = useState('usuario'); // usuario | contrasena | primera
  const [alias, setAlias] = useState('');
  const [contrasena, setContrasena] = useState('');
  const [confirmacion, setConfirmacion] = useState('');
  const [error, setError] = useState('');
  const [cargando, setCargando] = useState(false);

  if (sesionAlias) return <Navigate to="/" replace />;

  async function continuar(e) {
    e.preventDefault();
    setError('');
    const limpio = alias.trim();
    if (!/^[A-Za-z0-9_.-]{3,30}$/.test(limpio)) {
      setError('El usuario debe tener entre 3 y 30 caracteres: letras, números, punto, guion o guion bajo.');
      return;
    }
    setCargando(true);
    try {
      const { existe } = await verificarAlias(limpio);
      setAlias(limpio);
      setPaso(existe ? 'contrasena' : 'primera');
    } catch (err) {
      setError(err.message);
    } finally {
      setCargando(false);
    }
  }

  async function entrar(e) {
    e.preventDefault();
    setError('');
    if (paso === 'primera') {
      if (contrasena.length < 8) return setError('La contraseña debe tener al menos 8 caracteres.');
      if (contrasena !== confirmacion) return setError('La contraseña y su confirmación no coinciden.');
    }
    setCargando(true);
    try {
      const r = await acceder(alias, contrasena, paso === 'primera' ? confirmacion : undefined);
      iniciar(r.token, r.alias);
      navegar('/');
    } catch (err) {
      setError(err.status === 401 ? 'La contraseña no es correcta.' : err.message);
    } finally {
      setCargando(false);
    }
  }

  function cambiarUsuario() {
    setPaso('usuario');
    setError('');
    setContrasena('');
    setConfirmacion('');
  }

  const coincide = paso === 'primera' && confirmacion && contrasena === confirmacion;
  const textoBoton = cargando ? 'Un momento…' : paso === 'usuario' ? 'Continuar' : paso === 'primera' ? 'Acceder por primera vez' : 'Acceder';

  return (
    <div className="acceso">
      <aside className="acceso-lado">
        <Logo claro />
        <p className="acceso-lema">EXPLORACIÓN · IMAGEN · APRENDIZAJE</p>
        <h2>Un espacio para explorar la imagen.</h2>
        <p className="acceso-texto">
          Carga estudios de prueba, observa el proceso de segmentación y compara regiones de interés en un entorno académico experimental.
        </p>
        <Ilustracion />
        <ol className="acceso-pasos">
          <li>01 Cargar</li><li>02 Procesar</li><li>03 Visualizar</li>
        </ol>
        <p className="acceso-pie">Prosta-AI · Proyecto experimental de uso académico</p>
      </aside>

      <section className="acceso-form">
        <form onSubmit={paso === 'usuario' ? continuar : entrar} noValidate>
          <h1>Accede a Prosta-AI</h1>
          <p className="subtitulo">Introduce tus credenciales académicas para continuar al espacio de trabajo.</p>
          <Mensaje tipo="info">{aviso}</Mensaje>

          <Campo id="alias" etiqueta="Usuario" icono={User} valor={alias} onCambio={setAlias}
            placeholder="Tu usuario académico" autoComplete="username" autoFocus soloLectura={paso !== 'usuario'} />
          {paso !== 'usuario' && (
            <>
              <button type="button" className="enlace" onClick={cambiarUsuario}>Cambiar usuario</button>
              {paso === 'primera' && <p className="nota">Este usuario es nuevo. Elige una contraseña de al menos 8 caracteres.</p>}
              <Campo id="contrasena" etiqueta="Contraseña" icono={Lock} tipo="password" valor={contrasena}
                onCambio={setContrasena} placeholder="Tu contraseña" autoComplete={paso === 'primera' ? 'new-password' : 'current-password'} autoFocus />
            </>
          )}
          {paso === 'primera' && (
            <>
              <Campo id="confirmacion" etiqueta="Verificar contraseña" icono={Lock} tipo="password" valor={confirmacion}
                onCambio={setConfirmacion} placeholder="Ingresa nuevamente tu contraseña" autoComplete="new-password" />
              {coincide && <Mensaje tipo="ok">Las contraseñas coinciden.</Mensaje>}
            </>
          )}

          <Mensaje>{error}</Mensaje>
          <button className="btn btn-primario btn-ancho" disabled={cargando}>
            {textoBoton} <ArrowRight size={18} aria-hidden="true" />
          </button>
          <p className="acceso-nota">
            <ShieldCheck size={18} aria-hidden="true" />
            Utiliza únicamente archivos de prueba sin datos personales. El acceso no habilita un uso clínico.
          </p>
          <Aviso />
        </form>
      </section>
    </div>
  );
}
