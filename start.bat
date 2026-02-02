@echo off
REM =============================================================================
REM Script Universal de Arranque - Pollos Panchita (Windows)
REM =============================================================================
REM Este script detecta automaticamente si Docker esta disponible:
REM - Si Docker esta instalado: Usa Docker (NO requiere Python/pip)
REM - Si no: Usa ejecucion local con SQLite (requiere Python/pip)
REM Uso: start.bat o doble clic

setlocal enabledelayedexpansion

echo ============================================
echo Pollos Panchita - Arranque Automatico
echo Sistema: Windows
echo ============================================
echo.

REM =============================================================================
REM Detectar Docker
REM =============================================================================
echo [INFO] Detectando entorno de ejecucion...

set USE_DOCKER=0
where docker >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    docker info >nul 2>nul
    if !ERRORLEVEL! EQU 0 (
        set USE_DOCKER=1
        echo [OK] Docker detectado y corriendo

        REM Detectar docker-compose
        docker-compose --version >nul 2>nul
        if !ERRORLEVEL! EQU 0 (
            set DOCKER_COMPOSE=docker-compose
        ) else (
            docker compose version >nul 2>nul
            if !ERRORLEVEL! EQU 0 (
                set DOCKER_COMPOSE=docker compose
            ) else (
                echo [ADVERTENCIA] Docker Compose no encontrado
                set USE_DOCKER=0
            )
        )
    ) else (
        echo [ADVERTENCIA] Docker no esta corriendo
    )
) else (
    echo [ADVERTENCIA] Docker no disponible
)

REM =============================================================================
REM OPCION 1: Usar Docker
REM =============================================================================
if %USE_DOCKER% EQU 1 (
    echo.
    echo === Modo: Docker ===
    echo No se requiere Python ni pip en tu PC
    echo.
    echo Configuracion:
    echo   Red:           192.168.100.0/24
    echo   Web:           192.168.100.10:8000
    echo   Database:      192.168.100.20:3306
    echo   Puerto Web:    http://localhost:8000
    echo   Puerto MySQL:  localhost:3309
    echo.
    echo Como quieres iniciar?
    echo   1) Primer inicio / Reconstruir (recomendado)
    echo   2) Inicio rapido (usa imagenes existentes)
    echo   3) Segundo plano (detached)
    echo   4) Detener contenedores
    echo   5) Ver estado
    echo.

    set /p docker_option="Opcion [1-5, Enter=1]: "
    if "!docker_option!"=="" set docker_option=1

    if "!docker_option!"=="1" (
        echo.
        echo [INFO] Reconstruyendo e iniciando con Docker...
        echo Presiona Ctrl+C para detener
        echo.
        %DOCKER_COMPOSE% up --build
    ) else if "!docker_option!"=="2" (
        echo.
        echo [INFO] Iniciando con Docker...
        echo Presiona Ctrl+C para detener
        echo.
        %DOCKER_COMPOSE% up
    ) else if "!docker_option!"=="3" (
        echo.
        echo [INFO] Iniciando en segundo plano...
        %DOCKER_COMPOSE% up -d
        echo.
        echo [OK] Contenedores iniciados
        echo Acceso: http://localhost:8000
        echo Ver logs: docker-compose logs -f web
        echo Detener: docker-compose down
    ) else if "!docker_option!"=="4" (
        echo.
        echo [INFO] Deteniendo contenedores...
        %DOCKER_COMPOSE% down
        echo [OK] Detenidos
    ) else if "!docker_option!"=="5" (
        echo.
        echo Estado de contenedores:
        %DOCKER_COMPOSE% ps
    ) else (
        echo [ADVERTENCIA] Opcion invalida, usando opcion 1
        %DOCKER_COMPOSE% up --build
    )

    pause
    exit /b 0
)

REM =============================================================================
REM OPCION 2: Ejecucion Local (sin Docker)
REM =============================================================================
echo.
echo === Modo: Ejecucion Local (SQLite) ===
echo Requiere: Python 3.8+ y pip instalados
echo.

REM Detectar Python
where python >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    set PYTHON=python
) else (
    where python3 >nul 2>nul
    if %ERRORLEVEL% EQU 0 (
        set PYTHON=python3
    ) else (
        echo [ERROR] Python no encontrado
        echo.
        echo Opciones:
        echo   1. Instala Docker Desktop (recomendado)
        echo   2. Instala Python desde python.org
        pause
        exit /b 1
    )
)

REM Buscar entorno virtual
if exist ".venv\Scripts\python.exe" (
    set PYTHON=.venv\Scripts\python.exe
    set PIP=.venv\Scripts\pip.exe
    echo [OK] Usando venv: .venv
) else (
    set PIP=%PYTHON% -m pip
    echo [ADVERTENCIA] Usando Python del sistema
    echo Recomendacion: Crea un venv con: %PYTHON% -m venv .venv
)

REM Verificar Django
echo.
echo [INFO] Verificando dependencias...
%PYTHON% -c "import django" >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ADVERTENCIA] Django no instalado

    %PYTHON% -m pip --version >nul 2>nul
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] pip no esta instalado
        echo Mejor usa Docker: start.bat
        pause
        exit /b 1
    )

    echo [INFO] Instalando dependencias...
    %PIP% install -r requirements.txt
    if %ERRORLEVEL% NEQ 0 (
        pause
        exit /b 1
    )
)

echo [OK] Django instalado

REM Crear directorios
echo.
echo [INFO] Preparando estructura...
if not exist "media" mkdir media
if not exist "media\productos" mkdir media\productos
if not exist "backups" mkdir backups
if not exist "staticfiles" mkdir staticfiles
echo [OK] Directorios listos

REM Configurar SQLite
set DJANGO_USE_SQLITE=1
echo [OK] Base de datos: SQLite

REM Migraciones
echo.
echo [INFO] Ejecutando migraciones...
%PYTHON% manage.py migrate

REM Archivos estaticos
echo.
echo [INFO] Recopilando archivos estaticos...
%PYTHON% manage.py collectstatic --noinput --clear 2>nul

REM Informacion
echo.
echo === Informacion del Sistema ===
echo Sistema:       Windows
%PYTHON% --version
%PYTHON% -c "import django; print('Django:       ' + django.get_version())"
echo Base de datos: SQLite (db.sqlite3)

REM Iniciar servidor
echo.
echo === Iniciando Servidor ===
echo Acceso: http://127.0.0.1:8000
echo Presiona Ctrl+C para detener
echo.

%PYTHON% manage.py runserver

pause
