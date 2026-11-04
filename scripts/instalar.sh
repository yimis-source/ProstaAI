#!/usr/bin/env bash
# Instala dependencias, prepara la base de datos y descarga el modelo preentrenado.
set -euo pipefail
RAIZ="$(cd "$(dirname "$0")/.." && pwd)"
cd "$RAIZ/backend"
[ -d .venv ] || uv venv --python 3.12 .venv
uv pip install --python .venv -e '.[dev]' --index-strategy unsafe-best-match \
  --extra-index-url https://download.pytorch.org/whl/cpu
if [ ! -f .env ]; then
  sed "s#^PROSTA_SECRET_KEY=.*#PROSTA_SECRET_KEY=$(.venv/bin/python -c 'import secrets;print(secrets.token_hex(32))')#" .env.example > .env
  echo "Creado backend/.env con una clave secreta nueva"
fi
"$RAIZ/scripts/postgres_local.sh" iniciar
.venv/bin/alembic upgrade head
[ -f "$RAIZ/modelos/prostate_mri_anatomy/models/model.pt" ] || .venv/bin/python "$RAIZ/scripts/descargar_modelo.py"
cd "$RAIZ/frontend" && npm install
echo "Instalación completa. Para arrancar: scripts/arrancar.sh"
