#!/bin/bash
# Script para ejecutar migraciones - Pollos Panchita
# Ejecutar desde la carpeta PanchitaApp: ./migrar.sh
#
# Usa SQLite por defecto (sin MySQL/Docker).
# Para usar MySQL: quita DJANGO_USE_SQLITE=1 y asegúrate de tener MySQL corriendo.

set -e
cd "$(dirname "$0")"

echo "=== Migración Pollos Panchita ==="

# Detectar venv (priorizar macOS) - script está en PanchitaApp
if [ -d ".venv_mac/bin" ]; then
    PYTHON=".venv_mac/bin/python"
    echo "Usando venv: .venv_mac"
elif [ -d ".venv/bin" ]; then
    PYTHON=".venv/bin/python"
    echo "Usando venv: .venv"
elif [ -d "../.venv/bin" ]; then
    PYTHON="../.venv/bin/python"
    echo "Usando venv: ../.venv"
elif [ -d "../.venv/Scripts" ]; then
    echo "ERROR: El venv en .venv es de Windows (Scripts/)."
    echo "Crea un venv en macOS: python3 -m venv .venv_mac"
    echo "Luego: .venv_mac/bin/pip install -r requirements.txt"
    echo "Y ejecuta: ./migrar.sh"
    exit 1
else
    PYTHON="python3"
    echo "Usando python3 del sistema"
fi

# Verificar Django
if ! $PYTHON -c "import django" 2>/dev/null; then
    echo ""
    echo "ERROR: Django no está instalado."
    echo "Ejecuta: $PYTHON -m pip install -r requirements.txt"
    exit 1
fi

# Usar SQLite por defecto (no requiere MySQL)
export DJANGO_USE_SQLITE=1
echo "Base de datos: SQLite (db.sqlite3)"
echo ""

echo "Ejecutando migraciones..."
$PYTHON manage.py migrate

echo ""
echo "=== Migración completada ==="
