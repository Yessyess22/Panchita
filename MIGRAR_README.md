# Cómo ejecutar las migraciones

## Opción fácil: SQLite (sin MySQL/Docker)

El proyecto ahora usa **SQLite por defecto** cuando ejecutas `migrar.sh`. No necesitas MySQL ni Docker.

### Pasos

```bash
cd /Users/alex/Downloads/Panchita/PanchitaApp

# 1. Crear venv (solo la primera vez)
python3 -m venv .venv_mac

# 2. Instalar dependencias (solo la primera vez)
.venv_mac/bin/pip install -r requirements.txt

# 3. Ejecutar migraciones
./migrar.sh

# 4. Iniciar la app
./run_local.sh
```

O manualmente con SQLite:

```bash
export DJANGO_USE_SQLITE=1
.venv_mac/bin/python manage.py migrate
.venv_mac/bin/python manage.py runserver
```

## Opción: MySQL con Docker

Si prefieres usar MySQL:

```bash
# Iniciar MySQL
docker compose up -d db

# Esperar ~30 segundos, luego migrar (SIN DJANGO_USE_SQLITE)
unset DJANGO_USE_SQLITE
.venv_mac/bin/python manage.py migrate

# Iniciar la app
.venv_mac/bin/python manage.py runserver
```

## Scripts disponibles

- **`./migrar.sh`** – Ejecuta migraciones con SQLite
- **`./run_local.sh`** – Inicia el servidor con SQLite
