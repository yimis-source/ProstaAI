"""Cortes axiales en PNG desde NIfTI: imagen, máscara RGBA y exportación con aviso."""
import io
import textwrap
from abc import ABC, abstractmethod
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import nibabel as nib
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from prosta_ai.constantes import AVISO_EXPERIMENTAL

COLOR_ROI = (45, 212, 191)  # verde azulado del diseño de la interfaz
ALFA_ROI = 0.45
ANCHO_MINIMO_EXPORTAR = 512


_RUTA_FUENTE = Path(__file__).resolve().parent.parent / "recursos" / "DejaVuSans.ttf"


def _fuente(tam: int) -> ImageFont.FreeTypeFont:
    """Fuente con tildes y eñes para el aviso; si falta, la de Pillow."""
    try:
        return ImageFont.truetype(str(_RUTA_FUENTE), tam)
    except OSError:
        return ImageFont.load_default(size=tam)


@dataclass
class VolumenCortes:
    imagen: np.ndarray            # uint8, orientación canónica (x, y, z)
    mascara: np.ndarray | None    # bool, misma forma

    @property
    def forma(self) -> tuple[int, int, int]:
        return tuple(int(n) for n in self.imagen.shape)  # type: ignore[return-value]

    @property
    def cortes(self) -> int:
        return self.imagen.shape[2]


def _normalizar(datos: np.ndarray) -> np.ndarray:
    """Lleva la intensidad a 0-255 usando los percentiles 1 y 99."""
    p1, p99 = np.percentile(datos, [1, 99])
    if p99 <= p1:
        return np.zeros(datos.shape, dtype=np.uint8)
    return (np.clip((datos - p1) / (p99 - p1), 0, 1) * 255).astype(np.uint8)


def _leer(ruta: Path) -> np.ndarray:
    img = nib.as_closest_canonical(nib.load(str(ruta)))
    datos = np.asarray(img.get_fdata(dtype=np.float32))
    if datos.ndim == 4:
        datos = datos[..., 0]
    return datos


@lru_cache(maxsize=3)
def _cargar(ruta_imagen: str, ruta_mascara: str, marca: float) -> VolumenCortes:
    imagen = _normalizar(_leer(Path(ruta_imagen)))
    mascara = None
    if Path(ruta_mascara).exists():
        mascara = _leer(Path(ruta_mascara)) > 0.5
        if mascara.shape != imagen.shape:
            raise ValueError("La máscara no tiene la misma forma que la imagen")
    return VolumenCortes(imagen, mascara)


def cargar_volumen(ruta_imagen: Path, ruta_mascara: Path) -> VolumenCortes:
    marca = ruta_imagen.stat().st_mtime + (
        ruta_mascara.stat().st_mtime if ruta_mascara.exists() else 0
    )
    return _cargar(str(ruta_imagen), str(ruta_mascara), marca)


def _plano(arr2d: np.ndarray) -> np.ndarray:
    """Corte axial con la fila 0 arriba (y hacia arriba, x hacia la derecha)."""
    return np.rot90(arr2d)


class SliceRenderer(ABC):
    @abstractmethod
    def render(self, vol: VolumenCortes, indice: int) -> Image.Image: ...


class ImageSliceRenderer(SliceRenderer):
    def render(self, vol: VolumenCortes, indice: int) -> Image.Image:
        return Image.fromarray(_plano(vol.imagen[:, :, indice]), mode="L")


class MaskSliceRenderer(SliceRenderer):
    """RGBA transparente con la ROI en color."""

    def render(self, vol: VolumenCortes, indice: int) -> Image.Image:
        if vol.mascara is None:
            raise FileNotFoundError("No hay máscara")
        roi = _plano(vol.mascara[:, :, indice])
        rgba = np.zeros(roi.shape + (4,), dtype=np.uint8)
        rgba[roi] = (*COLOR_ROI, int(ALFA_ROI * 255))
        return Image.fromarray(rgba, mode="RGBA")


class OverlaySliceRenderer(SliceRenderer):
    """Imagen en gris con la ROI mezclada encima."""

    def render(self, vol: VolumenCortes, indice: int) -> Image.Image:
        base = Image.fromarray(_plano(vol.imagen[:, :, indice]), mode="L").convert("RGBA")
        if vol.mascara is not None:
            base = Image.alpha_composite(base, MaskSliceRenderer().render(vol, indice))
        return base.convert("RGB")


class AvisoDecorator(SliceRenderer):
    """Decorator: añade el aviso experimental impreso debajo de lo que dibuje el renderizador."""

    def __init__(self, renderer: SliceRenderer, aviso: str = AVISO_EXPERIMENTAL):
        self._renderer = renderer
        self._aviso = aviso

    def render(self, vol: VolumenCortes, indice: int) -> Image.Image:
        img = self._renderer.render(vol, indice).convert("RGB")
        factor = max(1, -(-ANCHO_MINIMO_EXPORTAR // img.width))
        if factor > 1:
            img = img.resize((img.width * factor, img.height * factor), Image.Resampling.BILINEAR)
        tam = max(12, img.width // 38)
        fuente = _fuente(tam)
        medidor = ImageDraw.Draw(img)
        max_chars = max(10, int(img.width / (tam * 0.55)))
        lineas = textwrap.wrap(self._aviso, width=max_chars)
        # Reajusta el ancho de línea con la medida real de la fuente
        while len(lineas) > 1 and max(medidor.textlength(l, font=fuente) for l in lineas) > img.width - 20:
            max_chars -= 2
            lineas = textwrap.wrap(self._aviso, width=max_chars)
        alto_linea = int(tam * 1.3)
        pie = Image.new("RGB", (img.width, alto_linea * len(lineas) + 16), (20, 20, 20))
        dib = ImageDraw.Draw(pie)
        for i, linea in enumerate(lineas):
            dib.text((10, 8 + i * alto_linea), linea, fill=(255, 255, 255), font=fuente)
        lienzo = Image.new("RGB", (img.width, img.height + pie.height))
        lienzo.paste(img, (0, 0))
        lienzo.paste(pie, (0, img.height))
        return lienzo


def a_png(img: Image.Image) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def renderizador_exportacion() -> SliceRenderer:
    return AvisoDecorator(OverlaySliceRenderer())
