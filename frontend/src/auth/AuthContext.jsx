import { createContext, useCallback, useContext, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { sesion, registrarAlExpirar } from '../api/cliente.js';

const AuthContext = createContext(null);
export const useAuth = () => useContext(AuthContext);

export function AuthProvider({ children }) {
  const navegar = useNavigate();
  const [alias, setAlias] = useState(sesion.alias());
  const [aviso, setAviso] = useState('');

  const iniciar = useCallback((token, nombre) => {
    sesion.guardar(token, nombre);
    setAlias(nombre);
    setAviso('');
  }, []);

  const cerrar = useCallback(
    (mensaje = '') => {
      sesion.borrar();
      setAlias(null);
      setAviso(mensaje);
      navegar('/acceso');
    },
    [navegar]
  );

  // Ante un 401 se vuelve a la pantalla de acceso
  useEffect(() => {
    registrarAlExpirar(() => cerrar('Su sesión terminó. Vuelva a ingresar.'));
  }, [cerrar]);

  return (
    <AuthContext.Provider value={{ alias, aviso, iniciar, cerrar }}>{children}</AuthContext.Provider>
  );
}
