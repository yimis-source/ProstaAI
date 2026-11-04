// Título, subtítulo y acción opcional de cada pantalla
export default function EncabezadoPagina({ titulo, subtitulo, children }) {
  return (
    <div className="encabezado">
      <div>
        <h1>{titulo}</h1>
        {subtitulo && <p className="subtitulo">{subtitulo}</p>}
      </div>
      {children && <div className="encabezado-accion">{children}</div>}
    </div>
  );
}
