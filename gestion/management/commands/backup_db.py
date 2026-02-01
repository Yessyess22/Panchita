"""
Comando para hacer backup de la base de datos.
Soporta MySQL (mysqldump) y SQLite (copia del archivo).

Uso:
  python manage.py backup_db
  python manage.py backup_db --dir=/ruta/backups

Para MySQL: requiere mysqldump instalado.
Para SQLite: copia db.sqlite3 a la carpeta de backups.
"""
import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Crea un backup de la base de datos (MySQL o SQLite).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dir',
            type=str,
            default=None,
            help='Carpeta donde guardar el backup (por defecto: backups/ en el proyecto)',
        )

    def handle(self, *args, **options):
        backup_dir = options.get('dir')
        if not backup_dir:
            backup_dir = Path(settings.BASE_DIR) / 'backups'
        else:
            backup_dir = Path(backup_dir)

        backup_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        db_settings = settings.DATABASES['default']
        engine = db_settings.get('ENGINE', '')

        if 'sqlite' in engine:
            self._backup_sqlite(db_settings, backup_dir, timestamp)
        elif 'mysql' in engine:
            self._backup_mysql(db_settings, backup_dir, timestamp)
        else:
            self.stderr.write(
                self.style.ERROR(f'Backup no implementado para: {engine}')
            )

    def _backup_sqlite(self, db_settings, backup_dir, timestamp):
        db_path = db_settings.get('NAME')
        if not db_path or not os.path.exists(db_path):
            self.stderr.write(
                self.style.ERROR(f'Archivo de base de datos no encontrado: {db_path}')
            )
            return

        dest = backup_dir / f'db_{timestamp}.sqlite3'
        shutil.copy2(db_path, dest)
        self.stdout.write(self.style.SUCCESS(f'✓ Backup SQLite guardado: {dest}'))

    def _backup_mysql(self, db_settings, backup_dir, timestamp):
        # Verificar que mysqldump esté disponible
        try:
            subprocess.run(['mysqldump', '--version'], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.stderr.write(
                self.style.ERROR(
                    'mysqldump no encontrado. Instale el cliente MySQL o MariaDB.'
                )
            )
            return

        name = db_settings.get('NAME')
        user = db_settings.get('USER')
        password = db_settings.get('PASSWORD', '')
        host = db_settings.get('HOST', 'localhost')
        port = db_settings.get('PORT', '3306')

        dest = backup_dir / f'db_{timestamp}.sql'

        cmd = [
            'mysqldump',
            '--single-transaction',
            '--quick',
            '--lock-tables=false',
            '-h', str(host),
            '-P', str(port),
            '-u', str(user),
            name,
        ]

        # Usar archivo temporal para la contraseña (más seguro que -p en línea)
        env = os.environ.copy()
        config_file = None
        if password:
            import tempfile
            fd, config_file = tempfile.mkstemp(suffix='.cnf', prefix='mysqldump_')
            try:
                with os.fdopen(fd, 'w') as f:
                    f.write(f'[client]\npassword={password}\n')
                cmd.extend(['--defaults-extra-file=' + config_file])
            except Exception:
                os.unlink(config_file) if config_file and os.path.exists(config_file) else None
                config_file = None

        try:
            with open(dest, 'w') as f:
                result = subprocess.run(
                    cmd,
                    stdout=f,
                    stderr=subprocess.PIPE,
                    env=env,
                    text=True,
                )
            if result.returncode != 0:
                self.stderr.write(
                    self.style.ERROR(f'mysqldump falló: {result.stderr}')
                )
                dest.unlink(missing_ok=True)
            else:
                self.stdout.write(self.style.SUCCESS(f'✓ Backup MySQL guardado: {dest}'))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Error al crear backup: {e}'))
        finally:
            if config_file and os.path.exists(config_file):
                try:
                    os.unlink(config_file)
                except OSError:
                    pass
