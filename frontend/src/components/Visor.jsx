import { useEffect, useState } from 'react';
import { Link2 } from 'lucide-react';
import { obtenerCorte } from '../api/index.js';

// Descarga un PNG (con token) y lo devuelve como URL local
function useImagen(idTrabajo, indice, capa) {
  const [url, setUrl] = useState(null);
  const [fallo, setFallo] = useState(false);
  useEffect(() => {
    if (!capa) return undefined;
    let activo = true;
    let actual = null;
    // Pequeña espera para no pedir cada corte al arrastrar el control
    const t = setTimeout(() => {
      obtenerCorte(idTrabajo, indice, capa)
        .then((blob) => {
          if (!activo) return;
          actual = URL.createObjectURL(blob);
          setUrl(actual);
          setFallo(false);
        })
        .catch(() => activo && setFallo(true));
    }, 60);
    return () => {
      activo = false;
      clearTimeout(t);
      if (actual) URL.revokeObjectURL(actual);
    };
  }, [idTrabajo, indice, capa]);
  return { url, fallo };
}

// Visor de un corte: imagen base y, opcionalmente, la máscara apilada encima
export default function Visor({ titulo, icono, etiqueta, idTrabajo, indice, total, conMascara, opacidad, zoom = 1, pie }) {
  const imagen = useImagen(idTrabajo, indice, 'imagen');
  const mascara = useImagen(idTrabajo, indice, conMascara ? 'mascara' : null);
  return (
    <figure className="visor">
      <figcaption className="visor-cabeza">
        <span className="visor-titulo">{icono} {titulo}</span>
        <span className="visor-etiqueta">{etiqueta}</span>
      </figcaption>
      <div className="visor-lienzo">
        <span className="visor-sync"><Link2 size={14} aria-hidden="true" /> SINCRONIZADO</span>
        <div className="visor-zoom" style={{ transform: `scale(${zoom})` }}>
          {imagen.url && <img src={imagen.url} alt={`${titulo}, corte ${indice + 1} de ${total}`} />}
          {conMascara && mascara.url && <img className="capa" src={mascara.url} alt="" style={{ opacity: opacidad }} />}
        </div>
        {(imagen.fallo || mascara.fallo) && <p className="visor-error">No se pudo cargar el corte.</p>}
        {!imagen.url && !imagen.fallo && <p className="visor-error">Cargando corte…</p>}
      </div>
      <div className="visor-pie">
        <span>Corte axial · {indice + 1} / {total}</span>
        <span>{pie}</span>
      </div>
    </figure>
  );
}
