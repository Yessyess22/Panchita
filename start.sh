#!/bin/bash
# =============================================================================
# Script Universal de Arranque - Pollos Panchita
# =============================================================================
# Este script detecta automáticamente si Docker está disponible:
# - Si Docker está instalado: Usa Docker (NO requiere Python/pip)
# - Si no: Usa ejecución local con SQLite (requiere Python/pip)
# Compatible con: Linux, macOS, Windows (Git Bash/WSL)
# Uso: ./start.sh

set -e
cd "$(dirname "$0")"

# =============================================================================
# Detectar Sistema Operativo
# =============================================================================
detect_os() {
    case "$(uname -s)" in
        Darwin*)    echo "mac";;
        Linux*)
            if grep -q Microsoft /proc/version 2>/dev/null; then
                echo "wsl"
            else
                echo "linux"
            fi
            ;;
        CYGWIN*|MINGW*|MSYS*)    echo "windows";;
        *)          echo "unknown";;
    esac
}

OS_TYPE=$(detect_os)

# Colores (deshabilitados en Windows)
if [ "$OS_TYPE" = "windows" ]; then
    RED=''; GREEN=''; YELLOW=''; BLUE=''; NC=''
else
    RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
fi

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}Pollos Panchita - Arranque Automático${NC}"
echo -e "${BLUE}Sistema: $OS_TYPE${NC}"
echo -e "${BLUE}============================================${NC}\n"

# =============================================================================
# Detectar Docker
# =============================================================================
echo -e "${BLUE}Detectando entorno de ejecución...${NC}"

USE_DOCKER=false
if command -v docker &> /dev/null && docker info &> /dev/null 2>&1; then
    USE_DOCKER=true
    echo -e "${GREEN}✓ Docker detectado y corriendo${NC}"

    # Detectar docker-compose
    if command -v docker-compose &> /dev/null; then
        DOCKER_COMPOSE="docker-compose"
    elif docker compose version &> /dev/null 2>&1; then
        DOCKER_COMPOSE="docker compose"
    else
        echo -e "${YELLOW}⚠ Docker Compose no encontrado, usando ejecución local${NC}"
        USE_DOCKER=false
    fi
else
    echo -e "${YELLOW}⚠ Docker no disponible, usando ejecución local${NC}"
fi

# =============================================================================
# OPCIÓN 1: Usar Docker
# =============================================================================
if [ "$USE_DOCKER" = true ]; then
    echo -e "\n${GREEN}=== Modo: Docker ===${NC}"
    echo -e "${BLUE}No se requiere Python ni pip en tu PC${NC}\n"

    echo -e "${BLUE}Configuración:${NC}"
    echo -e "  Red:           192.168.100.0/24"
    echo -e "  Web:           192.168.100.10:8000"
    echo -e "  Database:      192.168.100.20:3306"
    echo -e "  Puerto Web:    http://localhost:8000"
    echo -e "  Puerto MySQL:  localhost:3309"

    echo -e "\n${YELLOW}¿Cómo quieres iniciar?${NC}"
    echo -e "  1) Primer inicio / Reconstruir (recomendado)"
    echo -e "  2) Inicio rápido (usa imágenes existentes)"
    echo -e "  3) Segundo plano (detached)"
    echo -e "  4) Detener contenedores"
    echo -e "  5) Ver estado"

    read -p "Opción [1-5, Enter=1]: " docker_option
    docker_option=${docker_option:-1}

    case $docker_option in
        1)
            echo -e "\n${GREEN}Reconstruyendo e iniciando con Docker...${NC}"
            echo -e "${YELLOW}Presiona Ctrl+C para detener${NC}\n"
            $DOCKER_COMPOSE up --build
            ;;
        2)
            echo -e "\n${GREEN}Iniciando con Docker (sin rebuild)...${NC}"
            echo -e "${YELLOW}Presiona Ctrl+C para detener${NC}\n"
            $DOCKER_COMPOSE up
            ;;
        3)
            echo -e "\n${GREEN}Iniciando en segundo plano...${NC}"
            $DOCKER_COMPOSE up -d
            echo -e "\n${GREEN}✓ Contenedores iniciados${NC}"
            echo -e "${BLUE}Acceso:${NC} http://localhost:8000"
            echo -e "${YELLOW}Ver logs:${NC} docker-compose logs -f web"
            echo -e "${YELLOW}Detener:${NC} docker-compose down"
            ;;
        4)
            echo -e "\n${GREEN}Deteniendo contenedores...${NC}"
            $DOCKER_COMPOSE down
            echo -e "${GREEN}✓ Detenidos${NC}"
            ;;
        5)
            echo -e "\n${BLUE}Estado de contenedores:${NC}"
            $DOCKER_COMPOSE ps
            ;;
        *)
            echo -e "${RED}Opción inválida, usando opción 1${NC}"
            $DOCKER_COMPOSE up --build
            ;;
    esac

    exit 0
fi

# =============================================================================
# OPCIÓN 2: Ejecución Local (sin Docker)
# =============================================================================
echo -e "\n${GREEN}=== Modo: Ejecución Local (SQLite) ===${NC}"
echo -e "${YELLOW}Requiere: Python 3.8+ y pip instalados${NC}\n"

# Detectar Python y Virtual Environment
if [ "$OS_TYPE" = "mac" ] && [ -d ".venv_mac/bin" ]; then
    PYTHON=".venv_mac/bin/python"
    PIP=".venv_mac/bin/pip"
    echo -e "${GREEN}✓${NC} Usando venv: .venv_mac"
elif [ "$OS_TYPE" = "windows" ] && [ -d ".venv/Scripts" ]; then
    PYTHON=".venv/Scripts/python"
    PIP=".venv/Scripts/pip"
    echo -e "${GREEN}✓${NC} Usando venv: .venv (Windows)"
elif [ -d ".venv/bin" ]; then
    PYTHON=".venv/bin/python"
    PIP=".venv/bin/pip"
    echo -e "${GREEN}✓${NC} Usando venv: .venv"
else
    if command -v python3 &> /dev/null; then
        PYTHON="python3"
    elif command -v python &> /dev/null; then
        PYTHON="python"
    else
        echo -e "${RED}✗ Error: Python no encontrado${NC}"
        echo -e "${YELLOW}Opciones:${NC}"
        echo -e "  1. Instala Docker Desktop (recomendado)"
        echo -e "  2. Instala Python desde python.org"
        exit 1
    fi
    echo -e "${YELLOW}⚠${NC} Usando Python del sistema: $PYTHON"
    echo -e "${YELLOW}Recomendación: Crea un venv con: $PYTHON -m venv .venv${NC}"
fi

# Verificar Python
if ! command -v $PYTHON &> /dev/null; then
    echo -e "${RED}✗ Error: Python no encontrado${NC}"
    exit 1
fi

# Detectar PIP
if [ -z "$PIP" ]; then
    if command -v pip3 &> /dev/null; then
        PIP="pip3"
    elif command -v pip &> /dev/null; then
        PIP="pip"
    else
        PIP="$PYTHON -m pip"
    fi
fi

# Verificar Django
echo -e "\n${BLUE}Verificando dependencias...${NC}"
if ! $PYTHON -c "import django" 2>/dev/null; then
    echo -e "${YELLOW}⚠ Django no instalado${NC}"

    if ! $PYTHON -m pip --version &> /dev/null; then
        echo -e "${RED}✗ pip no está instalado${NC}"
        echo -e "${YELLOW}Mejor usa Docker: ./start.sh${NC}"
        exit 1
    fi

    echo -e "${BLUE}Instalando dependencias...${NC}"
    $PIP install -r requirements.txt || exit 1
fi

echo -e "${GREEN}✓${NC} Django instalado"

# Crear directorios
echo -e "\n${BLUE}Preparando estructura...${NC}"
for dir in media media/productos backups staticfiles; do
    mkdir -p "$dir"
    [ "$OS_TYPE" != "windows" ] && chmod 755 "$dir" 2>/dev/null || true
done
echo -e "${GREEN}✓${NC} Directorios listos"

# Configurar SQLite
export DJANGO_USE_SQLITE=1
echo -e "${GREEN}✓${NC} Base de datos: SQLite"

# Migraciones
echo -e "\n${BLUE}Ejecutando migraciones...${NC}"
$PYTHON manage.py migrate

# Archivos estáticos
echo -e "\n${BLUE}Recopilando archivos estáticos...${NC}"
$PYTHON manage.py collectstatic --noinput --clear 2>/dev/null || true

# Verificar datos
PRODUCT_COUNT=$($PYTHON -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panchita_project.settings')
django.setup()
from gestion.models import Producto
print(Producto.objects.count())
" 2>/dev/null || echo "0")

if [ "$PRODUCT_COUNT" -eq "0" ]; then
    echo -e "\n${YELLOW}⚠ Base de datos vacía${NC}"
    read -p "¿Cargar datos iniciales? (s/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Ss]$ ]]; then
        [ -f "load_products.py" ] && $PYTHON load_products.py
        [ -f "init_data.py" ] && $PYTHON init_data.py
    fi
else
    echo -e "\n${GREEN}✓${NC} Base de datos: $PRODUCT_COUNT productos"
fi

# Información
echo -e "\n${BLUE}=== Información del Sistema ===${NC}"
echo -e "Sistema:       $OS_TYPE"
echo -e "Python:        $($PYTHON --version 2>&1)"
echo -e "Django:        $($PYTHON -c 'import django; print(django.get_version())')"
echo -e "Base de datos: SQLite (db.sqlite3)"

# Iniciar servidor
echo -e "\n${GREEN}=== Iniciando Servidor ===${NC}"
echo -e "${BLUE}Acceso:${NC} http://127.0.0.1:8000"
echo -e "${YELLOW}Presiona Ctrl+C para detener${NC}\n"

$PYTHON manage.py runserver
