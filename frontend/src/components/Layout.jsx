import { useEffect, useState } from 'react';
import { NavLink, Outlet, useLocation } from 'react-router-dom';
import { FolderOpen, LayoutGrid, LogOut, Lock, Menu, MessagesSquare, Scan, Upload, Workflow } from 'lucide-react';
import { useAuth } from '../auth/AuthContext.jsx';
import Aviso from './Aviso.jsx';
import Logo from './Logo.jsx';

const ENLACES = [
  ['/', 'Inicio', LayoutGrid],
  ['/cargar', 'Cargar estudios', Upload],
  ['/procesamiento', 'Procesamiento', Workflow],
  ['/roi', 'Visualizar ROI', Scan],
  ['/estudios', 'Mis estudios', FolderOpen],
  ['/asistente', 'Asistente IA', MessagesSquare],
];

// Marco del espacio de trabajo: barra lateral, cabecera con miga de pan y pie con aviso
export default function Layout() {
  const { alias, cerrar } = useAuth();
  const [abierto, setAbierto] = useState(false);
  const { pathname } = useLocation();
  const actual = ENLACES.find(([ruta]) => (ruta === '/' ? pathname === '/' : pathname.startsWith(ruta)));

  // Cierra el menú móvil al navegar
  useEffect(() => setAbierto(false), [pathname]);

  return (
    <div className="marco">
      <header className="barra-movil">
        <button type="button" className="btn-menu" aria-label="Abrir o cerrar el menú"
          aria-expanded={abierto} aria-controls="menu-lateral" onClick={() => setAbierto(!abierto)}>
          <Menu size={22} aria-hidden="true" />
        </button>
        <Logo />
      </header>

      <nav id="menu-lateral" className={`menu ${abierto ? 'abierto' : ''}`} aria-label="Principal">
        <div className="menu-marca">
          <Logo />
          <p className="menu-sub">LABORATORIO ACADÉMICO</p>
        </div>
        <p className="menu-seccion">ESPACIO DE TRABAJO</p>
        <ul>
          {ENLACES.map(([ruta, texto, Icono]) => (
            <li key={ruta}>
              <NavLink to={ruta} end={ruta === '/'}>
                <Icono size={20} aria-hidden="true" />
                {texto}
              </NavLink>
            </li>
          ))}
        </ul>
        <div className="menu-pie">
          <div className="menu-entorno">
            <p><span className="punto" aria-hidden="true" /> <strong>Entorno experimental</strong></p>
            <p className="menu-nota">Solo uso académico</p>
          </div>
          <button type="button" className="menu-salir" onClick={() => cerrar()}>
            <LogOut size={20} aria-hidden="true" />
            Cerrar sesión
          </button>
        </div>
      </nav>

      <div className="contenido">
        <div className="cabecera">
          <nav aria-label="Ubicación" className="miga">
            <span>Prosta-AI</span>
            <span className="miga-sep" aria-hidden="true">/</span>
            <strong>{actual ? actual[1] : ''}</strong>
          </nav>
          <div className="cabecera-chips">
            <span className="chip chip-teal"><span className="punto" aria-hidden="true" /> Muestras de prueba</span>
            <span className="chip-sesion"><Lock size={16} aria-hidden="true" /> Sesión académica · <strong>{alias}</strong></span>
          </div>
        </div>
        <main id="principal">
          <Outlet />
        </main>
        <footer className="pie">
          <Aviso />
        </footer>
      </div>
    </div>
  );
}
