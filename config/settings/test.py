"""
With these settings, tests run faster.
"""

from .base import *  # noqa: F403
from .base import TEMPLATES
from .base import env

# GENERAL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#secret-key
SECRET_KEY = env(
    "DJANGO_SECRET_KEY",
    default="axGm5JTbuY404v1rZy9CyZIhAdMH4SUwvhOgXqXq6No5BY2YXGxjA5ElStIXevXz",
)
# https://docs.djangoproject.com/en/dev/ref/settings/#test-runner
TEST_RUNNER = "django.test.runner.DiscoverRunner"

# PASSWORDS
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#password-hashers
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# EMAIL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#email-backend
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# DEBUGGING FOR TEMPLATES
# ------------------------------------------------------------------------------
TEMPLATES[0]["OPTIONS"]["debug"] = True  # type: ignore[index]

# MEDIA
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#media-url
MEDIA_URL = "http://media.testserver/"
# Your stuff...
# ------------------------------------------------------------------------------
AXES_ENABLED = False

# Properly disable Django Axes for tests
if not AXES_ENABLED:
    # Remove Axes middleware
    MIDDLEWARE = [m for m in MIDDLEWARE if not m.startswith('axes.')]

    # Remove Axes authentication backend
    AUTHENTICATION_BACKENDS = [auth for auth in AUTHENTICATION_BACKENDS if not auth.startswith('axes.')]

    # Remove Axes from INSTALLED_APPS
    INSTALLED_APPS = [app for app in INSTALLED_APPS if app != 'axes']
