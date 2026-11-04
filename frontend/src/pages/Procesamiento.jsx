import { useCallback, useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { ArrowRight, Clock, Play, Scan, Timer } from 'lucide-react';
import { listarEstudios, obtenerTrabajo, procesarEstudio } from '../api/index.js';
import Aviso from '../components/Aviso.jsx';
import EncabezadoPagina from '../components/EncabezadoPagina.jsx';
import Pasos from '../components/Pasos.jsx';
import Etapas from '../components/Etapas.jsx';
import EtiquetaEstado from '../components/EtiquetaEstado.jsx';
import Mensaje from '../components/Mensaje.jsx';
import { formatearDuracion, formatearFechaCorta } from '../constantes.js';

const ACTIVO = ['pendiente', 'en proceso'];

export default function Procesamiento() {
  const [params, setParams] = useSearchParams();
  const [estudios, setEstudios] = useState([]);
  const [idEstudio, setIdEstudio] = useState(params.get('estudio') || '');
  const [trabajo, setTrabajo] = useState(null);
  const [error, setError] = useState('');
  const [enviando, setEnviando] = useState(false);

  const cargarLista = useCallback(
    () => listarEstudios().then(setEstudios).catch((e) => setError(e.message)),
    []
  );
  useEffect(() => { cargarLista(); }, [cargarLista]);

  const estudio = estudios.find((e) => String(e.id) === String(idEstudio));

  // Al cambiar de estudio se carga su último trabajo (si lo hay)
  useEffect(() => {
    setTrabajo(null);
    if (estudio && estudio.id_ultimo_trabajo) {
      obtenerTrabajo(estudio.id_ultimo_trabajo).then(setTrabajo).catch((e) => setError(e.message));
    }
    // solo depende del estudio elegido
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [estudio?.id, estudios.length]);

  // Consulta del trabajo cada 1,5 s mientras esté activo
  const idTrabajo = trabajo?.id;
  const activo = trabajo && ACTIVO.includes(trabajo.estado);
  useEffect(() => {
    if (!activo) return undefined;
    const t = setInterval(() => {
      obtenerTrabajo(idTrabajo)
        .then((n) => {
          setTrabajo(n);
          if (!ACTIVO.includes(n.estado)) cargarLista();
        })
        .catch((e) => setError(e.message));
    }, 1500);
    return () => clearInterval(t);
  }, [activo, idTrabajo, cargarLista]);

  // Reloj para el tiempo transcurrido mientras el trabajo está activo
  const [ahora, setAhora] = useState(Date.now());
  useEffect(() => {
    if (!activo) return undefined;
    const t = setInterval(() => setAhora(Date.now()), 1000);
    return () => clearInterval(t);
  }, [activo]);

  function elegir(valor) {
    setIdEstudio(valor);
    setError('');
    setParams(valor ? { estudio: valor } : {});
  }

  async function procesar() {
    setError('');
    setEnviando(true);
    try {
      const nuevo = await procesarEstudio(estudio.id);
      setTrabajo(await obtenerTrabajo(nuevo.id));
    } catch (e) {
      setError(e.message);
    } finally {
      setEnviando(false);
    }
  }

  const compatibles = estudios.filter((e) => e.estado !== 'no compatible');
  const falla = trabajo?.estado === 'fallido';
  const completo = trabajo?.estado === 'completado';
  const textoBoton = falla ? 'Volver a procesar' : completo ? 'Procesar de nuevo' : 'Procesar';

  // Avance derivado de las etapas completadas
  const hechas = (trabajo?.etapas || []).filter((e) => e.estado === 'completado').length;
  const porcentaje = Math.round((hechas / 5) * 100);
  const inicio = trabajo?.fecha_inicio ? new Date(trabajo.fecha_inicio).getTime() : null;
  const fin = trabajo?.fecha_fin ? new Date(trabajo.fecha_fin).getTime() : null;
  const transcurrido = inicio ? ((fin || ahora) - inicio) / 1000 : null;
  const hora = (iso) => new Date(iso).toLocaleTimeString('es', { hour12: false });

  return (
    <>
      <EncabezadoPagina titulo="Procesamiento del estudio" subtitulo="Consulta la ejecución y el estado de cada etapa del flujo experimental." />
      <Pasos actual={completo ? 3 : 2} />
      <Aviso />

      <section className="tarjeta selector">
        <label htmlFor="estudio">Estudio</label>
        <select id="estudio" value={idEstudio} onChange={(e) => elegir(e.target.value)}>
          <option value="">Selecciona un estudio</option>
          {compatibles.map((e) => (
            <option key={e.id} value={e.id}>{e.codigo} · {e.formato} · {e.estado}</option>
          ))}
        </select>
        {estudios.length === 0 && <p className="nota">No hay estudios. <Link to="/cargar">Cargar un estudio</Link></p>}
        <Mensaje>{error}</Mensaje>
      </section>

      {trabajo && estudio && (
        <div className="dos-columnas">
          <section className="tarjeta tarjeta-etapas">
            <div className="etapas-cabeza">
              <div>
                <h2 className="id-medio">{trabajo.codigo || estudio.codigo}</h2>
                <p className="nota">Estudio de prueba · {estudio.formato}</p>
              </div>
              <EtiquetaEstado estado={trabajo.estado} />
            </div>
            {/* Región que los lectores de pantalla anuncian al cambiar */}
            <div aria-live="polite">
              <div className="progreso-texto">
                <span>{completo ? 'Ejecución finalizada' : falla ? 'Ejecución detenida' : 'Ejecución en curso'}</span>
                <span>{porcentaje} %</span>
              </div>
              <div className="progreso" role="progressbar" aria-valuemin="0" aria-valuemax="100" aria-valuenow={porcentaje} aria-label="Avance del procesamiento">
                <span style={{ width: `${porcentaje}%` }} className={falla ? 'progreso-error' : ''} />
              </div>
              <Etapas etapas={trabajo.etapas} />
              {falla && (
                <Mensaje>
                  El procesamiento falló en la etapa «{trabajo.etapa_fallida || 'desconocida'}»:{' '}
                  {trabajo.mensaje_error || 'sin detalle disponible'}. Puedes corregir el estudio y volver a procesar.
                </Mensaje>
              )}
            </div>
            {inicio && (
              <p className="etapas-pie">
                <Clock size={16} aria-hidden="true" />
                {formatearFechaCorta(trabajo.fecha_inicio)} · Inicio {hora(trabajo.fecha_inicio)}
                {trabajo.fecha_fin && ` · Fin ${hora(trabajo.fecha_fin)}`}
              </p>
            )}
          </section>

          <aside>
            <section className="tarjeta">
              <h3 className="con-icono"><Timer size={18} aria-hidden="true" /> Tiempo transcurrido</h3>
              <p className="cifra-grande">{formatearDuracion(transcurrido)}</p>
              <p className="objetivo">Objetivo de tiempo: ≤ 2 min</p>
              <p className="nota">Es una meta experimental, no una garantía. El tiempo puede variar según los archivos y los recursos disponibles.</p>
            </section>
            {completo && (
              <section className="tarjeta tarjeta-teal">
                <Scan size={22} aria-hidden="true" />
                <h3>Listo para comparar</h3>
                <p>Abre el mismo corte de prueba con y sin superposición de ROI. La salida no implica certeza clínica.</p>
              </section>
            )}
          </aside>
        </div>
      )}

      <div className="barra-accion">
        <p className="barra-estado" aria-live="polite">
          {completo ? 'Las etapas han finalizado. Revisa ahora la ROI experimental.' : activo ? 'Procesando… se actualiza cada 1,5 segundos.' : 'Elige un estudio y pulsa Procesar.'}
        </p>
        <div className="acciones">
          <button type="button" className={`btn ${completo ? "btn-secundario" : "btn-primario"}`} onClick={procesar} disabled={!estudio || activo || enviando}>
            <Play size={18} aria-hidden="true" /> {enviando ? 'Enviando…' : textoBoton}
          </button>
          {completo && (
            <Link className="btn btn-primario" to={`/roi?trabajo=${trabajo.id}`}><ArrowRight size={18} aria-hidden="true" /> Ver resultados</Link>
          )}
        </div>
      </div>
    </>
  );
}
