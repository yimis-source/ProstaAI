import { useRef, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { ArrowRight, CircleCheck, CloudUpload, FileCheck2, FileX2, Plus, ShieldCheck, X } from 'lucide-react';
import { crearEstudio } from '../api/index.js';
import EncabezadoPagina from '../components/EncabezadoPagina.jsx';
import Mensaje from '../components/Mensaje.jsx';
import Pasos from '../components/Pasos.jsx';
import { formatearTamano } from '../constantes.js';

const esNifti = (f) => /\.(nii|nii\.gz)$/i.test(f.name);
const esDicom = (f) => /\.dcm$/i.test(f.name);
const esZip = (f) => /\.zip$/i.test(f.name);
const admitido = (f) => esNifti(f) || esDicom(f) || esZip(f);

// Reglas de combinación entre los archivos válidos; devuelve un mensaje o ''
function validar(validos) {
  if (validos.length === 0) return 'Selecciona al menos un archivo válido.';
  if (validos.every(esNifti)) {
    return validos.length === 1 ? '' : 'Para NIfTI se admite un solo archivo (.nii o .nii.gz).';
  }
  if (validos.length === 1 && esZip(validos[0])) return '';
  if (validos.every(esDicom)) return '';
  return 'No se pueden combinar formatos. Usa un archivo NIfTI, varios archivos DICOM (.dcm) o un .zip con la serie DICOM.';
}

// Zona para arrastrar/soltar o seleccionar archivos
function Zona({ id, titulo, ayuda, onAgregar, compacta }) {
  const entrada = useRef(null);
  const [encima, setEncima] = useState(false);
  const soltar = (e) => {
    e.preventDefault();
    setEncima(false);
    onAgregar([...e.dataTransfer.files]);
  };
  return (
    <div className={`zona ${compacta ? 'zona-compacta' : ''} ${encima ? 'zona-encima' : ''}`}
      onDragOver={(e) => { e.preventDefault(); setEncima(true); }}
      onDragLeave={() => setEncima(false)} onDrop={soltar}>
      {!compacta && <CloudUpload size={32} aria-hidden="true" />}
      <p className="zona-titulo">{titulo}</p>
      <p className="nota">{ayuda}</p>
      <input ref={entrada} id={id} type="file" multiple hidden
        onChange={(e) => { onAgregar([...e.target.files]); e.target.value = ''; }} />
      <label htmlFor={id} className="btn btn-secundario" tabIndex={0}
        onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && (e.preventDefault(), entrada.current.click())}>
        <Plus size={18} aria-hidden="true" /> Seleccionar archivos
      </label>
    </div>
  );
}

function FilaArchivo({ archivo, valido, subido, onQuitar }) {
  return (
    <li className={`archivo ${valido ? '' : 'archivo-excluido'}`}>
      <span className="archivo-icono">{valido ? <FileCheck2 size={20} aria-hidden="true" /> : <FileX2 size={20} aria-hidden="true" />}</span>
      <div className="archivo-datos">
        <span className="archivo-nombre">{archivo.name}</span>
        <span className="archivo-sub">{formatearTamano(archivo.size)} · {valido ? (subido ? 'Cargado' : 'Listo para cargar') : 'Formato no admitido'}</span>
      </div>
      <span className="archivo-estado">{valido ? '' : 'Excluido'}</span>
      <button type="button" className="icono-boton" onClick={onQuitar} aria-label={`Quitar ${archivo.name}`} disabled={subido}>
        <X size={18} aria-hidden="true" />
      </button>
    </li>
  );
}

export default function Cargar() {
  const navegar = useNavigate();
  const [archivos, setArchivos] = useState([]);
  const [referencia, setReferencia] = useState([]);
  const [error, setError] = useState('');
  const [creado, setCreado] = useState(null);
  const [enviando, setEnviando] = useState(false);

  const validos = archivos.filter(admitido);
  const excluidos = archivos.length - validos.length;
  const tamano = validos.reduce((s, f) => s + f.size, 0);

  async function enviar() {
    setError('');
    const problema = validar(validos);
    if (problema) return setError(problema);
    setEnviando(true);
    try {
      setCreado(await crearEstudio(validos, referencia));
    } catch (e) {
      setError(`El estudio fue rechazado: ${e.message}`);
    } finally {
      setEnviando(false);
    }
  }

  return (
    <>
      <EncabezadoPagina titulo="Cargar estudios" subtitulo="Añade archivos de prueba para preparar un estudio anónimo." />
      <Pasos actual={1} />

      <div className="dos-columnas">
        <div>
          <Zona id="archivos" titulo="Arrastra tus archivos de prueba aquí"
            ayuda="NIfTI (.nii, .nii.gz) un solo archivo · DICOM (.dcm) varios archivos o un .zip"
            onAgregar={(n) => { setCreado(null); setArchivos((a) => [...a, ...n]); }} />

          {archivos.length > 0 && (
            <section className="tarjeta tarjeta-lista">
              <div className="tarjeta-lista-cabeza">
                <h2>Archivos seleccionados</h2>
                <span className="chip"><span className="punto" aria-hidden="true" /> {validos.length} {validos.length === 1 ? 'válido' : 'válidos'}{excluidos > 0 && ` · ${excluidos} excluido${excluidos > 1 ? 's' : ''}`}</span>
              </div>
              <ul className="lista-archivos">
                {archivos.map((f, i) => (
                  <FilaArchivo key={f.name + i} archivo={f} valido={admitido(f)} subido={Boolean(creado)}
                    onQuitar={() => setArchivos(archivos.filter((_, k) => k !== i))} />
                ))}
              </ul>
            </section>
          )}

          <section className="tarjeta">
            <h2>Máscara de referencia (opcional)</h2>
            <p className="nota">Si la incluyes, se calcularán Dice e IoU al procesar.</p>
            <Zona id="referencia" compacta titulo="Archivo NIfTI con la misma forma que la imagen" ayuda="Selecciona o arrastra la máscara."
              onAgregar={(n) => setReferencia((a) => [...a, ...n])} />
            {referencia.length > 0 && (
              <ul className="lista-archivos">
                {referencia.map((f, i) => (
                  <FilaArchivo key={f.name + i} archivo={f} valido subido={Boolean(creado)}
                    onQuitar={() => setReferencia(referencia.filter((_, k) => k !== i))} />
                ))}
              </ul>
            )}
          </section>
        </div>

        <aside>
          <section className="tarjeta">
            <h2>Estudio de prueba</h2>
            <p className="etiqueta-mini">ID ANÓNIMO ASIGNADO</p>
            <p className="id-grande">{creado ? creado.codigo : 'Se asigna al cargar'}</p>
            <dl className="datos">
              <div><dt>Archivos válidos</dt><dd>{validos.length}</dd></div>
              <div><dt>Tamaño total</dt><dd>{formatearTamano(tamano)}</dd></div>
            </dl>
            {excluidos > 0 && <p className="nota">Los archivos excluidos no se incluirán en el procesamiento.</p>}
          </section>
          <section className="tarjeta tarjeta-teal">
            <ShieldCheck size={22} aria-hidden="true" />
            <h3>Se eliminan metadatos identificables o se rechaza el archivo</h3>
            <p>Usa únicamente archivos de prueba sin datos personales. No incluyas nombres en los archivos.</p>
          </section>
        </aside>
      </div>

      <Mensaje>{error}</Mensaje>
      <div className="barra-accion">
        {creado ? (
          <>
            <p className="barra-estado"><CircleCheck size={20} aria-hidden="true" /> Estudio {creado.codigo} cargado ({creado.formato}). Estado: {creado.estado}.</p>
            <div className="acciones">
              <Link className="btn btn-secundario" to="/estudios">Ver mis estudios</Link>
              <button type="button" className="btn btn-primario" onClick={() => navegar(`/procesamiento?estudio=${creado.id}`)}>
                <ArrowRight size={18} aria-hidden="true" /> Continuar a procesamiento
              </button>
            </div>
          </>
        ) : (
          <>
            <p className="barra-estado">{validos.length > 0 ? `${validos.length} ${validos.length === 1 ? 'archivo válido' : 'archivos válidos'}. Listo para cargar el estudio.` : 'Aún no hay archivos seleccionados.'}</p>
            <button type="button" className="btn btn-primario" onClick={enviar} disabled={enviando || validos.length === 0}>
              <CloudUpload size={18} aria-hidden="true" /> {enviando ? 'Subiendo…' : 'Cargar estudio'}
            </button>
          </>
        )}
      </div>
    </>
  );
}
