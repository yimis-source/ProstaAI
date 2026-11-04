import sys
from pathlib import Path

# la carpeta `entrenamiento/` está en la raíz del repositorio, fuera del paquete del backend
RAIZ = Path(__file__).resolve().parents[3]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))
