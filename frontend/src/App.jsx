import { Navigate, Route, Routes } from 'react-router-dom';
import { useAuth } from './auth/AuthContext.jsx';
import Layout from './components/Layout.jsx';
import Acceso from './pages/Acceso.jsx';
import Inicio from './pages/Inicio.jsx';
import Cargar from './pages/Cargar.jsx';
import Procesamiento from './pages/Procesamiento.jsx';
import VisualizarRoi from './pages/VisualizarRoi.jsx';
import MisEstudios from './pages/MisEstudios.jsx';
import Asistente from './pages/Asistente.jsx';

// Protege las rutas del espacio de trabajo
function Privada({ children }) {
  const { alias } = useAuth();
  return alias ? children : <Navigate to="/acceso" replace />;
}

export default function App() {
  return (
    <Routes>
      <Route path="/acceso" element={<Acceso />} />
      <Route
        element={
          <Privada>
            <Layout />
          </Privada>
        }
      >
        <Route path="/" element={<Inicio />} />
        <Route path="/cargar" element={<Cargar />} />
        <Route path="/procesamiento" element={<Procesamiento />} />
        <Route path="/roi" element={<VisualizarRoi />} />
        <Route path="/estudios" element={<MisEstudios />} />
        <Route path="/asistente" element={<Asistente />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
