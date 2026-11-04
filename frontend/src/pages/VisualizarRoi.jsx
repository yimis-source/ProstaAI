import { useCallback, useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { ChevronLeft, ChevronRight, FolderOpen, Image as IconoImagen, Minus, Plus, RotateCcw, Scan } from 'lucide-react';
import { exportarImagen, listarEstudios, obtenerResultado } from '../api/index.js';
import Aviso from '../components/Aviso.jsx';
import EncabezadoPagina from '../components/EncabezadoPagina.jsx';
import Pasos from '../components/Pasos.jsx';
import Mensaje from '../components/Mensaje.jsx';
import PanelExplicativo from '../components/PanelExplicativo.jsx';
import Visor from '../components/Visor.jsx';
import { SIN_REFERENCIA, formatearMetrica, formatearDuracion } from '../constantes.js';

// Selector cuando se entra sin un trabajo concreto
function Selector() {
  const [estudios, setEstudios] = useState(null);
  const [error, setError] = useState('');
  useEffect(() => {
    listarEstudios().then(setEstudios).catch((e) => setError(e.message));
  }, []);
  const listos = (estudios || []).filter((e) => e.estado === 'completado' && e.id_ultimo_trabajo);
  return (
    <section className="tarjeta">
      <h2>Elija un estudio procesado</h2>
      <Mensaje>{error}</Mensaje>
      {estudios && listos.length === 0 && (
        <p>No hay resultados todavía. <Link to="/procesamiento">Ir a procesamiento</Link></p>
      )}
      <ul className="lista-simple">
        {listos.map((e) => (
          <li key={e.id}>
            <Link className="btn btn-secundario" to={`/roi?trabajo=${e.id_ultimo_trabajo}`}>{e.codigo} · Ver ROI</Link>
          </li>
        ))}
      </ul>
    </section>
  );
}

function Visualizador({ idTrabajo }) {
  const [res, setRes] = useState(null);
  const [error, setError] = useState('');
  const [corte, setCorte] = useState(0);
  const [opacidad, setOpacidad] = useState(0.6);
  const [roiVisible, setRoiVisible] = useState(true);
  const [zoom, setZoom] = useState(1);

  useEffect(() => {
    setRes(null);
    obtenerResultado(idTrabajo)
      .then((r) => { setRes(r); setCorte(Math.floor(r.cortes / 2)); })
      .catch((e) => setError(e.message));
  }, [idTrabajo]);

  const mover = useCallback(
    (d) => res && setCorte((c) => Math.min(res.cortes - 1, Math.max(0, c + d))),
    [res]
  );

  // Flechas del teclado cambian el corte (salvo dentro de campos de formulario)
  useEffect(() => {
    const tecla = (e) => {
      if (['INPUT', 'SELECT', 'TEXTAREA'].includes(e.target.tagName)) return;
      if (e.key === 'ArrowRight' || e.key === 'ArrowUp') { e.preventDefault(); mover(1); }
      if (e.key === 'ArrowLeft' || e.key === 'ArrowDown') { e.preventDefault(); mover(-1); }
    };
    window.addEventListener('keydown', tecla);
    return () => window.removeEventListener('keydown', tecla);
  }, [mover]);

  async function exportar() {
    try {
      const blob = await exportarImagen(idTrabajo);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `roi-${res.codigo}.png`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      setError(e.message);
    }
  }

  if (error && !res) return <Mensaje>{error}</Mensaje>;
  if (!res) return <p>Cargando resultado…</p>;

  const dice = formatearMetrica(res.dice);
  const iou = formatearMetrica(res.iou);

  const subir = () => setZoom((z) => Math.min(3, +(z + 0.25).toFixed(2)));
  const bajar = () => setZoom((z) => Math.max(1, +(z - 0.25).toFixed(2)));

  return (
    <>
      <section className="barra-visor" aria-label="Controles del visor">
        <div className="control">
          <label htmlFor="corte" className="control-etq">Corte</label>
          <button type="button" className="icono-boton borde" onClick={() => mover(-1)} aria-label="Corte anterior"><ChevronLeft size={16} aria-hidden="true" /></button>
          <span className="control-valor" aria-live="polite">{corte + 1} / {res.cortes}</span>
          <button type="button" className="icono-boton borde" onClick={() => mover(1)} aria-label="Corte siguiente"><ChevronRight size={16} aria-hidden="true" /></button>
          <input id="corte" type="range" min="0" max={res.cortes - 1} value={corte} onChange={(e) => setCorte(Number(e.target.value))} />
        </div>
        <div className="control control-centro">
          <span className="control-etq" id="etq-roi">ROI</span>
          <button type="button" role="switch" aria-checked={roiVisible} aria-labelledby="etq-roi"
            className={`interruptor ${roiVisible ? 'activo' : ''}`} onClick={() => setRoiVisible(!roiVisible)}><span /></button>
          <label htmlFor="opacidad" className="control-etq suave">Opacidad</label>
          <input id="opacidad" type="range" min="0" max="1" step="0.05" value={opacidad} disabled={!roiVisible}
            onChange={(e) => setOpacidad(Number(e.target.value))} />
          <span className="control-valor teal">{Math.round(opacidad * 100)} %</span>
        </div>
        <div className="control">
          <span className="control-etq suave">Zoom</span>
          <button type="button" className="icono-boton borde" onClick={bajar} aria-label="Reducir zoom" disabled={zoom <= 1}><Minus size={16} aria-hidden="true" /></button>
          <span className="control-valor">{Math.round(zoom * 100)} %</span>
          <button type="button" className="icono-boton borde" onClick={subir} aria-label="Aumentar zoom" disabled={zoom >= 3}><Plus size={16} aria-hidden="true" /></button>
          <button type="button" className="icono-boton borde" onClick={() => setZoom(1)} aria-label="Restablecer zoom"><RotateCcw size={16} aria-hidden="true" /></button>
        </div>
      </section>

      <div className="visores">
        <Visor titulo="Original" icono={<IconoImagen size={18} aria-hidden="true" />} etiqueta={res.codigo}
          idTrabajo={idTrabajo} indice={corte} total={res.cortes} zoom={zoom} pie="Sin superposición" />
        <Visor titulo="Original + ROI" icono={<Scan size={18} aria-hidden="true" />} etiqueta={res.codigo}
          idTrabajo={idTrabajo} indice={corte} total={res.cortes} zoom={zoom} conMascara={roiVisible} opacidad={opacidad}
          pie={roiVisible ? <><span className="punto" aria-hidden="true" /> ROI experimental · {Math.round(opacidad * 100)} %</> : 'ROI oculta'} />
      </div>
      <p className="nota nota-visores">Misma imagen, mismo corte y mismo zoom en ambos paneles. La ROI solo se superpone en el segundo visor. Puedes cambiar de corte con las flechas del teclado.</p>

      <section className="tarjeta">
        <h2>Métricas del resultado</h2>
        {dice === null ? (
          <p>{SIN_REFERENCIA}</p>
        ) : (
          <dl className="metricas">
            <div><dt>Dice</dt><dd>{dice}</dd></div>
            <div><dt>IoU</dt><dd>{iou}</dd></div>
          </dl>
        )}
        <p className="nota">Modelo: {res.modelo?.nombre} {res.modelo?.version} · Tiempo total: {formatearDuracion(res.tiempo_total_s)}</p>
        <Mensaje>{error}</Mensaje>
        <div className="acciones">
          <button type="button" className="btn btn-primario" onClick={exportar}>Exportar imagen</button>
        </div>
      </section>
      <PanelExplicativo />
    </>
  );
}

export default function VisualizarRoi() {
  const [params] = useSearchParams();
  const idTrabajo = params.get('trabajo');
  return (
    <>
      <EncabezadoPagina titulo="Visualizar y comparar ROI"
        subtitulo={idTrabajo ? 'Compara la imagen original con la ROI propuesta por el modelo experimental.' : 'Elige un estudio procesado para comparar su ROI.'}>
        <Link className="btn btn-secundario" to="/estudios"><FolderOpen size={18} aria-hidden="true" /> Mis estudios</Link>
      </EncabezadoPagina>
      <Pasos actual={3} />
      <Aviso />
      {idTrabajo ? <Visualizador idTrabajo={idTrabajo} /> : <Selector />}
    </>
  );
}
