"""
Settings para usar SQLite (sin MySQL).
Uso: python manage.py migrate --settings=panchita_project.settings_sqlite
O:   DJANGO_USE_SQLITE=1 python manage.py migrate
"""
from .settings import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',  # Archivo persistente
    }
}
