#!/usr/bin/env bash
# Arranca PostgreSQL local, la API (con la tarea de procesamiento) y el frontend.
set -euo pipefail
RAIZ="$(cd "$(dirname "$0")/.." && pwd)"
"$RAIZ/scripts/postgres_local.sh" iniciar
cd "$RAIZ/backend"
.venv/bin/alembic upgrade head
.venv/bin/uvicorn prosta_ai.api.app:create_app --factory --port 8000 &
API=$!
trap 'kill $API 2>/dev/null' EXIT
cd "$RAIZ/frontend"
echo "Abra http://localhost:5173"
npx vite --port 5173
