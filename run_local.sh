#!/bin/bash
# Ejecutar la app con SQLite (sin MySQL/Docker)
# Uso: ./run_local.sh

set -e
cd "$(dirname "$0")"

# Detectar venv
if [ -d ".venv_mac/bin" ]; then
    PYTHON=".venv_mac/bin/python"
elif [ -d ".venv/bin" ]; then
    PYTHON=".venv/bin/python"
elif [ -d "../.venv/bin" ]; then
    PYTHON="../.venv/bin/python"
else
    PYTHON="python3"
fi

export DJANGO_USE_SQLITE=1
echo "Iniciando servidor (SQLite)..."
$PYTHON manage.py runserver
