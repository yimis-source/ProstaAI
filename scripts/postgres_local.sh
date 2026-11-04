#!/usr/bin/env bash
# Clúster PostgreSQL local para desarrollo, sin permisos de administrador.
# Uso: scripts/postgres_local.sh iniciar|detener|estado
set -euo pipefail
RAIZ="$(cd "$(dirname "$0")/.." && pwd)"
DATOS="$RAIZ/.pgdata"
PUERTO="${PROSTA_PG_PUERTO:-5433}"

case "${1:-iniciar}" in
  iniciar)
    if [ ! -d "$DATOS" ]; then
      initdb -D "$DATOS" -U prosta --auth=trust -E UTF8 --locale=C >/dev/null
    fi
    if ! pg_ctl -D "$DATOS" status >/dev/null 2>&1; then
      pg_ctl -D "$DATOS" -l "$DATOS/servidor.log" -o "-p $PUERTO -k /tmp -c listen_addresses=localhost" start >/dev/null
      sleep 1
    fi
    psql -h localhost -p "$PUERTO" -U prosta -d postgres -tc "SELECT 1 FROM pg_database WHERE datname='prosta_ai'" | grep -q 1 \
      || createdb -h localhost -p "$PUERTO" -U prosta prosta_ai
    echo "PostgreSQL activo en localhost:$PUERTO (base prosta_ai, usuario prosta)"
    ;;
  detener) pg_ctl -D "$DATOS" stop ;;
  estado) pg_ctl -D "$DATOS" status ;;
  *) echo "Uso: $0 iniciar|detener|estado"; exit 1 ;;
esac
