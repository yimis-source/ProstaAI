"""Almacenamiento privado de archivos (fuera de la base de datos)."""
import hashlib
import shutil
from pathlib import Path
from typing import BinaryIO

# Extensiones que se conservan; cualquier otra se reemplaza por .bin
_EXTENSIONES = (".nii.gz", ".nii", ".dcm", ".zip")
_CHUNK = 1024 * 1024


def extension_segura(nombre: str) -> str:
    bajo = nombre.lower()
    for ext in _EXTENSIONES:
        if bajo.endswith(ext):
            return ext
    return ".bin"


class PrivateStorage:
    def __init__(self, root: Path):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def absoluta(self, ruta_relativa: str) -> Path:
        ruta = (self.root / ruta_relativa).resolve()
        if self.root not in ruta.parents and ruta != self.root:
            raise ValueError("Ruta fuera del almacenamiento")
        return ruta

    def relativa(self, ruta: Path) -> str:
        return Path(ruta).resolve().relative_to(self.root).as_posix()

    def guardar_archivo(
        self, codigo: str, tipo: str, numero: int, nombre_original: str, origen: BinaryIO
    ) -> tuple[str, int, str]:
        """Guarda con nombre neutro (nunca el original). Devuelve (ruta, tamaño, sha256)."""
        prefijo = "archivo" if tipo == "imagen" else "referencia"
        nombre = f"{prefijo}_{numero:03d}{extension_segura(nombre_original)}"
        carpeta = self.root / "estudios" / codigo / tipo
        carpeta.mkdir(parents=True, exist_ok=True)
        destino = carpeta / nombre
        sha = hashlib.sha256()
        tamano = 0
        with open(destino, "wb") as f:
            while bloque := origen.read(_CHUNK):
                f.write(bloque)
                sha.update(bloque)
                tamano += len(bloque)
        return self.relativa(destino), tamano, sha.hexdigest()

    def carpeta_resultado(self, id_trabajo: int) -> Path:
        carpeta = self.root / "resultados" / str(id_trabajo)
        carpeta.mkdir(parents=True, exist_ok=True)
        return carpeta

    def borrar_estudio(self, codigo: str) -> None:
        shutil.rmtree(self.root / "estudios" / codigo, ignore_errors=True)

    def borrar_resultado(self, id_trabajo: int) -> None:
        shutil.rmtree(self.root / "resultados" / str(id_trabajo), ignore_errors=True)
