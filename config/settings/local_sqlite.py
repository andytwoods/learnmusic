# ruff: noqa: E501
from .local import *  # noqa: F403,F401
from .base import BASE_DIR

# Override database to use SQLite for local development
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "local_db.sqlite3",
    }
}

# Keep connection settings consistent with base
DATABASES["default"]["CONN_MAX_AGE"] = 60
DATABASES["default"]["ATOMIC_REQUESTS"] = True
