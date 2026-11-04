import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, ArrowUpRight, FlaskConical, Files, MessagesSquare, Plus, Scan, Upload, Workflow } from 'lucide-react';
import { listarEstudios } from '../api/index.js';
import EncabezadoPagina from '../components/EncabezadoPagina.jsx';
import EtiquetaEstado from '../components/EtiquetaEstado.jsx';
import Mensaje from '../components/Mensaje.jsx';
import { formatearFechaCorta } from '../constantes.js';

function Tarjeta({ num, icono: Icono, titulo, texto, enlace, ruta, nota }) {
  return (
    <section className="tarjeta tarjeta-paso">
      <div className="tarjeta-cabeza">
        <span className="icono-caja"><Icono size={22} aria-hidden="true" /></span>
        <span className="tarjeta-num">{num}</span>
      </div>
      <h2>{titulo}</h2>
      <p className="tarjeta-texto">{texto}</p>
      <Link className="tarjeta-enlace" to={ruta}>{enlace} <ArrowRight size={18} aria-hidden="true" /></Link>
      <p className="tarjeta-nota">{nota}</p>
    </section>
  );
}

export default function Inicio() {
  const [estudios, setEstudios] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    listarEstudios().then(setEstudios).catch((e) => setError(e.message));
  }, []);

  const lista = estudios || [];
  const recientes = [...lista].sort((a, b) => b.id - a.id).slice(0, 5);
  const listos = lista.filter((e) => e.estado === 'listo para procesar').length;
  const ultimoRoi = [...lista].sort((a, b) => b.id - a.id).find((e) => e.estado === 'completado');

  return (
    <>
      <EncabezadoPagina titulo="Tu espacio de exploración" subtitulo="Del archivo de prueba a la comparación de ROI, en un mismo entorno.">
        <Link className="btn btn-primario" to="/cargar"><Plus size={18} aria-hidden="true" /> Cargar un estudio</Link>
      </EncabezadoPagina>

      <div className="banda-teal">
        <FlaskConical size={22} aria-hidden="true" />
        <div>
          <strong>Explora con muestras, no con datos personales</strong>
          <p>Las ROI generadas son experimentales. Úsalas para observar el flujo y sus limitaciones.</p>
        </div>
        <span className="banda-chip"><span className="punto" aria-hidden="true" /> Uso académico</span>
      </div>

      <div className="tarjetas">
        <Tarjeta num="01" icono={Upload} titulo="Cargar un estudio" texto="Añade archivos de prueba y comprueba su validación antes de procesar."
          enlace="Cargar archivos" ruta="/cargar" nota="DICOM · NIfTI" />
        <Tarjeta num="02" icono={Workflow} titulo="Procesar un estudio" texto="Revisa las etapas de preparación, segmentación y generación de ROI."
          enlace="Ir a procesamiento" ruta="/procesamiento"
          nota={`${listos} ${listos === 1 ? 'estudio listo' : 'estudios listos'} para procesar`} />
        <Tarjeta num="03" icono={Scan} titulo="Visualizar ROI" texto="Compara la imagen original y su ROI en visores sincronizados."
          enlace="Abrir comparador" ruta="/roi" nota={ultimoRoi ? `${ultimoRoi.codigo} disponible` : 'Aún sin resultados'} />
      </div>

      <div className="encabezado encabezado-seccion">
        <div>
          <h2 className="titulo-seccion">Últimos estudios</h2>
          <p className="subtitulo">Continúa desde tu actividad más reciente.</p>
        </div>
        <Link className="btn btn-secundario" to="/estudios"><ArrowUpRight size={18} aria-hidden="true" /> Ver todos los estudios</Link>
      </div>

      <Mensaje>{error}</Mensaje>
      {estudios === null && !error && <p>Cargando…</p>}
      {estudios && recientes.length === 0 && <p className="nota">Todavía no has cargado estudios.</p>}
      {recientes.length > 0 && (
        <div className="tabla-scroll">
          <table>
            <thead>
              <tr><th>ID anónimo</th><th>Fecha de carga</th><th>Estado</th><th>Acción</th></tr>
            </thead>
            <tbody>
              {recientes.map((e) => (
                <tr key={e.id}>
                  <td>
                    <div className="celda-id">
                      <Files size={20} aria-hidden="true" />
                      <div><span className="id">{e.codigo}</span><span className="sub">{e.formato}</span></div>
                    </div>
                  </td>
                  <td>{formatearFechaCorta(e.fecha_carga)}</td>
                  <td><EtiquetaEstado estado={e.estado} /></td>
                  <td>
                    {e.estado === 'completado' && e.id_ultimo_trabajo ? (
                      <Link className="enlace-accion" to={`/roi?trabajo=${e.id_ultimo_trabajo}`}>Ver ROI <ArrowUpRight size={14} aria-hidden="true" /></Link>
                    ) : e.estado !== 'no compatible' ? (
                      <Link className="enlace-accion" to={`/procesamiento?estudio=${e.id}`}>Procesar <ArrowUpRight size={14} aria-hidden="true" /></Link>
                    ) : '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <p className="ayuda-asistente">
        <MessagesSquare size={18} aria-hidden="true" />
        ¿Primera vez aquí? El Asistente IA puede orientarte sobre el uso de la app.{' '}
        <Link to="/asistente" className="enlace-accion">Abrir asistente <ArrowRight size={14} aria-hidden="true" /></Link>
      </p>
    </>
  );
}
