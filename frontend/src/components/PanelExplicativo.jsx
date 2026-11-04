import { CircleHelp } from 'lucide-react';

// Explicación de la ROI y las métricas (RF-17)
export default function PanelExplicativo() {
  return (
    <section className="tarjeta panel-info" aria-labelledby="t-info">
      <div>
        <h2 id="t-info" className="con-icono"><CircleHelp size={20} aria-hidden="true" /> ¿Qué estoy viendo?</h2>
        <p>
          Una ROI (región de interés) es la zona que el modelo experimental propone como próstata en cada corte.
          El contorno de color permite explorar su ubicación sobre esta muestra de prueba.
        </p>
        <p>
          Dice e IoU miden cuánto coincide la ROI con una máscara de referencia. Van de 0 a 1: valores cercanos a 1
          indican mayor coincidencia. Solo se calculan si el estudio incluye esa máscara.
        </p>
      </div>
      <div>
        <h2>Cómo leerla y cuáles son sus límites</h2>
        <p>
          La superposición puede ser imprecisa y no implica un hallazgo. No aporta certeza clínica ni una medida de riesgo.
          Oculta la ROI o ajusta su opacidad para contrastarla con el original.
        </p>
        <p>
          Las métricas dependen de la calidad de la referencia. Este resultado no es un diagnóstico ni sustituye
          la valoración de un profesional de la salud.
        </p>
      </div>
    </section>
  );
}
