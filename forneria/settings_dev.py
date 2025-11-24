from .settings import *
from pathlib import Path

# Si `BASE_DIR` no está definido en settings.py, crearlo aquí como fallback
try:
    BASE_DIR
except NameError:
    BASE_DIR = Path(__file__).resolve().parent.parent

# Desarrollo local: usar SQLite para poder levantar la aplicación sin MySQL
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# Ajustes convenientes para desarrollo
# En entornos locales normalmente DEBUG=True, pero podemos desactivarlo
# para que Django muestre páginas de error estándar (500/404). Ten en
# cuenta que con DEBUG=False el servidor de desarrollo no sirve archivos
# estáticos automáticamente y debes configurar `ALLOWED_HOSTS` correctamente.
DEBUG = False
ALLOWED_HOSTS = ["127.0.0.1", "localhost"]

# Evitar sobrescribir secretos de producción aquí. Usa este archivo solo en desarrollo local.