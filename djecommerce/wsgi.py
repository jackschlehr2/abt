import os

from django.core.wsgi import get_wsgi_application

DEVELOPMENT_MODE = os.getenv("DEVELOPMENT_MODE", "False") == "True"
if DEVELOPMENT_MODE:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE',
                          'djecommerce.settings.development')
else:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE',
                          'djecommerce.settings.production')

application = get_wsgi_application()
