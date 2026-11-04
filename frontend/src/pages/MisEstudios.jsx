import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowDownWideNarrow, ArrowUpRight, ChevronDown, ChevronLeft, ChevronRight, FolderPlus, Files, Info, Plus,
  Scan, Search, ShieldCheck, Trash2, Upload, Workflow } from 'lucide-react';
import { eliminarEstudio, listarEstudios } from '../api/index.js';
import Aviso from '../components/Aviso.jsx';
import EncabezadoPagina from '../components/EncabezadoPagina.jsx';
import EtiquetaEstado from '../components/EtiquetaEstado.jsx';
import Mensaje from '../components/Mensaje.jsx';
import { capitalizar, formatearFechaCorta, formatearMetrica } from '../constantes.js';

const POR_PAGINA = 10;
const PESTANAS = [
  ['todos', 'Todos', () => true],
  ['completados', 'Completados', (e) => e.estado === 'completado'],
  ['listos', 'Listos para procesar', (e) => e.estado === 'listo para procesar'],
  ['no', 'No compatibles', (e) => e.estado === 'no compatible'],
];
const ESTADOS = ['completado', 'listo para procesar', 'pendiente', 'en proceso', 'fallido', 'no compatible'];
const FECHAS = [['', 'Todas las fechas'], ['7', 'Últimos 7 días'], ['30', 'Últimos 30 días']];

function Estadistica({ titulo, valor, nota, icono: Icono }) {
  return (
    <section className="tarjeta estadistica">
      <div>
        <p className="estadistica-titulo">{titulo}</p>
        <p className="estadistica-valor">{String(valor).padStart(2, '0')}</p>
        <p className="nota">{nota}</p>
      </div>
      <span className="icono-caja"><Icono size={20} aria-hidden="true" /></span>
    </section>
  );
}

export default function MisEstudios() {
  const [estudios, setEstudios] = useState(null);
  const [error, setError] = useState('');
  const [aEliminar, setAEliminar] = useState(null);
  const [pestana, setPestana] = useState('todos');
  const [busqueda, setBusqueda] = useState('');
  const [estado, setEstado] = useState('');
  const [dias, setDias] = useState('');
  const [pagina, setPagina] = useState(1);

  const cargar = () => listarEstudios().then(setEstudios).catch((e) => setError(e.message));
  useEffect(() => { cargar(); }, []);

  const lista = estudios || [];
  const filtrados = useMemo(() => {
    const filtroPestana = PESTANAS.find((p) => p[0] === pestana)[2];
    const limite = dias ? Date.now() - Number(dias) * 86400000 : 0;
    return lista
      .filter(filtroPestana)
      .filter((e) => !estado || e.estado === estado)
      .filter((e) => !busqueda || e.codigo.toLowerCase().includes(busqueda.trim().toLowerCase()))
      .filter((e) => !limite || new Date(e.fecha_carga).getTime() >= limite)
      .sort((a, b) => new Date(b.fecha_carga) - new Date(a.fecha_carga));
  }, [lista, pestana, busqueda, estado, dias]);

  const paginas = Math.max(1, Math.ceil(filtrados.length / POR_PAGINA));
  const actual = Math.min(pagina, paginas);
  const visibles = filtrados.slice((actual - 1) * POR_PAGINA, actual * POR_PAGINA);

  async function confirmar() {
    try {
      await eliminarEstudio(aEliminar.id);
      setAEliminar(null);
      await cargar();
    } catch (e) {
      setError(e.message);
      setAEliminar(null);
    }
  }

  const conteo = (f) => lista.filter(f).length;
  const vacio = estudios && estudios.length === 0;

  return (
    <>
      <EncabezadoPagina titulo="Mis estudios" subtitulo="Consulta tus muestras de prueba y retoma la exploración de sus ROI.">
        <Link className="btn btn-primario" to="/cargar"><Plus size={18} aria-hidden="true" /> Cargar un estudio</Link>
      </EncabezadoPagina>
      <Aviso />
      <Mensaje>{error}</Mensaje>
      {estudios === null && !error && <p>Cargando…</p>}

      {estudios && !vacio && (
        <div className="tarjetas">
          <Estadistica titulo="Estudios de prueba" valor={lista.length} nota="Identificadores anónimos" icono={Files} />
          <Estadistica titulo="ROI disponibles" valor={conteo(PESTANAS[1][2])} nota="Salidas experimentales" icono={Scan} />
          <Estadistica titulo="Listo para procesar" valor={conteo(PESTANAS[2][2])} nota="Estudios preparados" icono={Workflow} />
        </div>
      )}

      {estudios && (
        <>
          <div className="pestanas" role="tablist" aria-label="Filtrar por estado">
            {(vacio ? PESTANAS.slice(0, 3) : PESTANAS).map(([id, texto, f]) => (
              <button key={id} type="button" role="tab" aria-selected={pestana === id} className={`pestana ${pestana === id ? 'activa' : ''}`}
                onClick={() => { setPestana(id); setPagina(1); }}>
                {texto} ({conteo(f)})
              </button>
            ))}
          </div>

          <div className="filtros">
            <div className="campo-caja filtro-busqueda">
              <Search size={18} aria-hidden="true" />
              <input type="search" aria-label="Buscar por ID anónimo" placeholder="Buscar por ID anónimo" value={busqueda}
                onChange={(e) => { setBusqueda(e.target.value); setPagina(1); }} />
            </div>
            <div className="campo-select">
              <select aria-label="Filtrar por estado" value={estado} onChange={(e) => { setEstado(e.target.value); setPagina(1); }}>
                <option value="">Todos los estados</option>
                {ESTADOS.map((x) => <option key={x} value={x}>{capitalizar(x)}</option>)}
              </select>
              <ChevronDown size={16} aria-hidden="true" />
            </div>
            <div className="campo-select">
              <select aria-label="Filtrar por fecha" value={dias} onChange={(e) => { setDias(e.target.value); setPagina(1); }}>
                {FECHAS.map(([v, t]) => <option key={v} value={v}>{t}</option>)}
              </select>
              <ChevronDown size={16} aria-hidden="true" />
            </div>
            {!vacio && <span className="orden"><ArrowDownWideNarrow size={18} aria-hidden="true" /> Más recientes primero</span>}
          </div>
        </>
      )}

      {vacio && (
        <>
          <section className="tarjeta vacio">
            <span className="icono-caja icono-grande"><FolderPlus size={34} aria-hidden="true" /></span>
            <h2>Aún no hay estudios</h2>
            <p>Carga tu primer estudio de prueba para recorrer el flujo de procesamiento y explorar una ROI experimental.</p>
            <Link className="btn btn-primario" to="/cargar"><Upload size={18} aria-hidden="true" /> Cargar un estudio</Link>
            <p className="nota">Solo archivos de prueba sin datos personales</p>
          </section>
          <div className="dos-iguales">
            <section className="tarjeta tarjeta-info"><Files size={22} aria-hidden="true" />
              <div><h3>Prepara tus archivos</h3><p>Puedes seleccionar varios archivos DICOM o NIfTI. Se validarán antes del procesamiento.</p></div></section>
            <section className="tarjeta tarjeta-info"><ShieldCheck size={22} aria-hidden="true" />
              <div><h3>Trabaja con IDs anónimos</h3><p>Cada estudio recibe un identificador. No añadas nombres ni información personal a los archivos.</p></div></section>
          </div>
        </>
      )}

      {estudios && !vacio && (
        <>
          {visibles.length === 0 ? (
            <section className="tarjeta vacio"><p>Ningún estudio coincide con los filtros.</p></section>
          ) : (
            <div className="tabla-scroll">
              <table>
                <thead>
                  <tr><th>ID anónimo</th><th>Formato</th><th>Fecha de carga</th><th>Estado</th><th>Dice</th><th>Acción</th></tr>
                </thead>
                <tbody>
                  {visibles.map((e) => (
                    <tr key={e.id}>
                      <td><div className="celda-id"><Files size={20} aria-hidden="true" /><span className="id">{e.codigo}</span></div></td>
                      <td>{e.formato}</td>
                      <td>{formatearFechaCorta(e.fecha_carga)}</td>
                      <td><EtiquetaEstado estado={e.estado} /></td>
                      <td>{formatearMetrica(e.dice) ?? '—'}</td>
                      <td>
                        <div className="celda-acciones">
                          {e.estado === 'completado' && e.id_ultimo_trabajo && (
                            <Link className="enlace-accion" to={`/roi?trabajo=${e.id_ultimo_trabajo}`}>Ver ROI <ArrowUpRight size={14} aria-hidden="true" /></Link>
                          )}
                          {e.estado !== 'no compatible' && (
                            <Link className="enlace-accion" to={`/procesamiento?estudio=${e.id}`}>
                              {e.estado === 'completado' ? 'Ver detalles' : 'Procesar / Ver detalles'} <ArrowUpRight size={14} aria-hidden="true" />
                            </Link>
                          )}
                          <button type="button" className="icono-boton peligro" onClick={() => setAEliminar(e)} aria-label={`Eliminar ${e.codigo}`}>
                            <Trash2 size={18} aria-hidden="true" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          <div className="paginacion">
            <span className="nota">Mostrando {filtrados.length ? (actual - 1) * POR_PAGINA + 1 : 0}–{(actual - 1) * POR_PAGINA + visibles.length} de {filtrados.length} estudios</span>
            <div className="acciones">
              <button type="button" className="btn btn-suave" disabled={actual <= 1} onClick={() => setPagina(actual - 1)}><ChevronLeft size={16} aria-hidden="true" /> Anterior</button>
              <span className="pagina-actual" aria-current="page">{actual}</span>
              <button type="button" className="btn btn-suave" disabled={actual >= paginas} onClick={() => setPagina(actual + 1)}>Siguiente <ChevronRight size={16} aria-hidden="true" /></button>
            </div>
          </div>
          <p className="nota nota-icono"><Info size={16} aria-hidden="true" /> «—» indica que el estudio aún no tiene máscara de referencia evaluada o no fue procesado.</p>
        </>
      )}

      {aEliminar && (
        <div className="modal-fondo">
          <div className="modal" role="alertdialog" aria-modal="true" aria-labelledby="t-elim">
            <h2 id="t-elim">Eliminar estudio</h2>
            <p>¿Eliminar {aEliminar.codigo}? Se borrarán sus archivos y resultados. Esta acción no se puede deshacer.</p>
            <div className="acciones">
              <button type="button" className="btn btn-peligro" onClick={confirmar} autoFocus>Sí, eliminar</button>
              <button type="button" className="btn btn-secundario" onClick={() => setAEliminar(null)}>Cancelar</button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
