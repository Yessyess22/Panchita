#!/bin/bash
# =============================================================================
# Script de Arranque Local - Pollos Panchita
# =============================================================================
# Ejecuta la aplicación con SQLite (sin MySQL/Docker)
# Realiza verificaciones de permisos, migraciones y configuración inicial
# Uso: ./run_local.sh

set -e
cd "$(dirname "$0")"

# =============================================================================
# Colores para output
# =============================================================================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# =============================================================================
# Detectar Python y Virtual Environment
# =============================================================================
echo -e "${BLUE}=== Pollos Panchita - Inicialización Local ===${NC}\n"

if [ -d ".venv_mac/bin" ]; then
    PYTHON=".venv_mac/bin/python"
    PIP=".venv_mac/bin/pip"
    echo -e "${GREEN}✓${NC} Usando venv: .venv_mac"
elif [ -d ".venv/bin" ]; then
    PYTHON=".venv/bin/python"
    PIP=".venv/bin/pip"
    echo -e "${GREEN}✓${NC} Usando venv: .venv"
elif [ -d "../.venv/bin" ]; then
    PYTHON="../.venv/bin/python"
    PIP="../.venv/bin/pip"
    echo -e "${GREEN}✓${NC} Usando venv: ../.venv"
else
    PYTHON="python3"
    PIP="pip3"
    echo -e "${YELLOW}⚠${NC} Usando python3 del sistema"
fi

# Verificar Python
if ! command -v $PYTHON &> /dev/null; then
    echo -e "${RED}✗ Error: Python no encontrado${NC}"
    exit 1
fi

# =============================================================================
# Verificar Dependencias de Django
# =============================================================================
echo -e "\n${BLUE}Verificando dependencias...${NC}"
if ! $PYTHON -c "import django" 2>/dev/null; then
    echo -e "${RED}✗ Django no está instalado${NC}"
    echo -e "${YELLOW}Instalando dependencias...${NC}"
    $PIP install -r requirements.txt
fi

# =============================================================================
# Crear y Verificar Directorios Necesarios
# =============================================================================
echo -e "\n${BLUE}Verificando estructura de directorios...${NC}"

REQUIRED_DIRS=(
    "media"
    "media/productos"
    "backups"
    "staticfiles"
    "gestion/static"
    "gestion/templates"
)

for dir in "${REQUIRED_DIRS[@]}"; do
    if [ ! -d "$dir" ]; then
        echo -e "${YELLOW}⚠${NC} Creando directorio: $dir"
        mkdir -p "$dir"
        chmod 755 "$dir"
    else
        echo -e "${GREEN}✓${NC} Directorio existe: $dir"
    fi
done

# =============================================================================
# Verificar Permisos de Escritura
# =============================================================================
echo -e "\n${BLUE}Verificando permisos de escritura...${NC}"

WRITABLE_DIRS=(
    "media"
    "media/productos"
    "backups"
    "staticfiles"
)

for dir in "${WRITABLE_DIRS[@]}"; do
    if [ -w "$dir" ]; then
        echo -e "${GREEN}✓${NC} Permiso de escritura OK: $dir"
    else
        echo -e "${RED}✗${NC} Sin permiso de escritura: $dir"
        echo -e "${YELLOW}Intentando corregir permisos...${NC}"
        chmod 755 "$dir" 2>/dev/null || {
            echo -e "${RED}Error: No se pudo corregir permisos en $dir${NC}"
            echo "Ejecuta: sudo chmod 755 $dir"
        }
    fi
done

# Verificar permiso en archivos críticos
WRITABLE_FILES=(
    "db.sqlite3"
)

for file in "${WRITABLE_FILES[@]}"; do
    if [ -f "$file" ]; then
        if [ -w "$file" ]; then
            echo -e "${GREEN}✓${NC} Permiso de escritura OK: $file"
        else
            echo -e "${YELLOW}⚠${NC} Ajustando permisos: $file"
            chmod 644 "$file"
        fi
    fi
done

# =============================================================================
# Configurar Entorno Django
# =============================================================================
export DJANGO_USE_SQLITE=1
echo -e "\n${GREEN}✓${NC} Base de datos: SQLite (db.sqlite3)"

# =============================================================================
# Ejecutar Migraciones
# =============================================================================
echo -e "\n${BLUE}Ejecutando migraciones de base de datos...${NC}"
$PYTHON manage.py migrate

# =============================================================================
# Recopilar Archivos Estáticos (opcional)
# =============================================================================
echo -e "\n${BLUE}Recopilando archivos estáticos...${NC}"
$PYTHON manage.py collectstatic --noinput --clear 2>/dev/null || {
    echo -e "${YELLOW}⚠${NC} No se pudo recopilar archivos estáticos (opcional)"
}

# =============================================================================
# Verificar Datos Iniciales
# =============================================================================
echo -e "\n${BLUE}Verificando datos iniciales...${NC}"

# Verificar si existen productos en la base de datos
PRODUCT_COUNT=$($PYTHON -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panchita_project.settings')
django.setup()
from gestion.models import Producto
print(Producto.objects.count())
" 2>/dev/null || echo "0")

if [ "$PRODUCT_COUNT" -eq "0" ]; then
    echo -e "${YELLOW}⚠${NC} No hay productos en la base de datos"
    read -p "¿Deseas cargar datos iniciales? (s/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Ss]$ ]]; then
        if [ -f "load_products.py" ]; then
            echo -e "${BLUE}Cargando productos...${NC}"
            $PYTHON load_products.py
        fi
        if [ -f "init_data.py" ]; then
            echo -e "${BLUE}Cargando datos iniciales...${NC}"
            $PYTHON init_data.py
        fi
    fi
else
    echo -e "${GREEN}✓${NC} Base de datos contiene $PRODUCT_COUNT productos"
fi

# =============================================================================
# Información del Sistema
# =============================================================================
echo -e "\n${BLUE}=== Información del Sistema ===${NC}"
echo -e "Python:        $($PYTHON --version)"
echo -e "Django:        $($PYTHON -c 'import django; print(django.get_version())')"
echo -e "Directorio:    $(pwd)"
echo -e "Base de datos: SQLite (db.sqlite3)"

# =============================================================================
# Iniciar Servidor de Desarrollo
# =============================================================================
echo -e "\n${GREEN}=== Iniciando Servidor de Desarrollo ===${NC}"
echo -e "${BLUE}Acceso:${NC} http://127.0.0.1:8000"
echo -e "${YELLOW}Presiona Ctrl+C para detener el servidor${NC}\n"

$PYTHON manage.py runserver
