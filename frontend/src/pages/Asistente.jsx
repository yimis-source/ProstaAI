import { useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, ArrowUp, ArrowUpRight, Check, Info, MessagesSquare, ShieldCheck, SquarePen } from 'lucide-react';
import { preguntarAsistente } from '../api/index.js';
import EncabezadoPagina from '../components/EncabezadoPagina.jsx';
import Mensaje from '../components/Mensaje.jsx';

const SALUDO = 'Hola. Puedo ayudarte a cargar archivos de prueba, seguir el procesamiento y usar el comparador de ROI. ¿Qué te gustaría explorar?';
const SUGERENCIAS = [
  '¿Qué formatos puedo cargar?',
  '¿Qué significa cada etapa del procesamiento?',
  '¿Cómo cambio de corte o ajusto la opacidad?',
];
const AYUDA = ['Carga y validación de archivos', 'Navegación por el flujo', 'Controles del comparador', 'Limitaciones de la ROI'];
// Mensaje del asistente: introducción, pasos numerados, separador y nota; si faltan, el texto completo
function Burbuja({ mensaje: m }) {
  if (m.de === 'usuario' || !m.intro) return <p className="burbuja">{m.texto}</p>;
  return (
    <div className="burbuja burbuja-estructurada">
      <p className="burbuja-intro">{m.intro}</p>
      {m.pasos.length > 0 && (
        <ol className="burbuja-pasos">
          {m.pasos.map((p, k) => (
            <li key={k}><span className="paso-insignia" aria-hidden="true">{k + 1}</span><span>{p}</span></li>
          ))}
        </ol>
      )}
      {m.nota && <p className="burbuja-nota">{m.nota}</p>}
    </div>
  );
}

const INICIO = [{ de: 'asistente', texto: SALUDO }];

export default function Asistente() {
  const [mensajes, setMensajes] = useState(INICIO);
  const [pregunta, setPregunta] = useState('');
  const [error, setError] = useState('');
  const [enviando, setEnviando] = useState(false);
  const fin = useRef(null);

  useEffect(() => { fin.current?.scrollIntoView?.({ block: 'nearest' }); }, [mensajes]);

  async function preguntar(texto) {
    const limpio = texto.trim();
    if (!limpio || enviando) return;
    setError('');
    setPregunta('');
    setMensajes((m) => [...m, { de: 'usuario', texto: limpio }]);
    setEnviando(true);
    try {
      const r = await preguntarAsistente(limpio);
      setMensajes((m) => [...m, {
        de: 'asistente', texto: r.respuesta, intro: r.intro, pasos: r.pasos || [], nota: r.nota,
        enlace: r.enlace, sugerencias: r.sugerencias || [],
      }]);
    } catch (err) {
      setError(err.message);
    } finally {
      setEnviando(false);
    }
  }

  return (
    <>
      <EncabezadoPagina titulo="Asistente IA" subtitulo="Orientación opcional para usar Prosta-AI y comprender su flujo de trabajo.">
        <button type="button" className="btn btn-secundario" onClick={() => { setMensajes(INICIO); setError(''); }}>
          <SquarePen size={18} aria-hidden="true" /> Nueva conversación
        </button>
      </EncabezadoPagina>
      <div className="aviso">
        <Info size={18} aria-hidden="true" />
        <p>No ofrece interpretación clínica <span className="separador" aria-hidden="true" /> Responde sobre controles, archivos y etapas de la aplicación.</p>
      </div>

      <div className="dos-columnas">
        <section className="tarjeta chat">
          <div className="chat-cabeza">
            <span className="icono-caja"><MessagesSquare size={20} aria-hidden="true" /></span>
            <div><strong>Asistente de uso</strong><p className="nota">Ayuda sobre Prosta-AI</p></div>
            <span className="chip"><span className="punto" aria-hidden="true" /> Experimental</span>
          </div>
          <div className="chat-mensajes" aria-live="polite">
            {mensajes.map((m, i) => (
              <div key={i} className={`mensaje-chat mensaje-chat-${m.de}`}>
                <span className="burbuja-autor">{m.de === 'usuario' ? 'TÚ' : 'PROSTA-AI'}</span>
                <Burbuja mensaje={m} />
                {m.enlace && (
                  <Link className="btn btn-secundario btn-chat" to={m.enlace.ruta}>
                    {m.enlace.texto} <ArrowRight size={16} aria-hidden="true" />
                  </Link>
                )}
                {i === mensajes.length - 1 && m.sugerencias?.length > 0 && (
                  <div className="chips-chat" role="group" aria-label="Preguntas sugeridas">
                    {m.sugerencias.map((q) => (
                      <button key={q} type="button" className="chip-chat" onClick={() => preguntar(q)} disabled={enviando}>{q}</button>
                    ))}
                  </div>
                )}
              </div>
            ))}
            <div ref={fin} />
          </div>
          <Mensaje>{error}</Mensaje>
          <form onSubmit={(e) => { e.preventDefault(); preguntar(pregunta); }} className="chat-form">
            <label htmlFor="pregunta" className="solo-lectores">Tu pregunta</label>
            <input id="pregunta" value={pregunta} onChange={(e) => setPregunta(e.target.value)} autoComplete="off"
              placeholder="Pregunta sobre el uso de Prosta-AI…" />
            <button className="btn-enviar" disabled={enviando || !pregunta.trim()} aria-label="Enviar pregunta">
              <ArrowUp size={18} aria-hidden="true" />
            </button>
          </form>
          <p className="nota chat-nota">No incluyas datos personales. Las respuestas pueden contener errores.</p>
        </section>

        <aside>
          <h2 className="titulo-seccion">Puedes preguntar</h2>
          <div className="sugerencias">
            {SUGERENCIAS.map((s) => (
              <button key={s} type="button" className="sugerencia" onClick={() => preguntar(s)} disabled={enviando}>
                {s} <ArrowUpRight size={14} aria-hidden="true" />
              </button>
            ))}
          </div>
          <section className="tarjeta">
            <h3>En qué puede ayudarte</h3>
            <ul className="lista-check">
              {AYUDA.map((a) => <li key={a}><Check size={16} aria-hidden="true" /> {a}</li>)}
            </ul>
          </section>
          <p className="nota nota-icono"><ShieldCheck size={18} aria-hidden="true" /> Este asistente no evalúa imágenes ni determina el significado clínico de una ROI.</p>
        </aside>
      </div>
    </>
  );
}
