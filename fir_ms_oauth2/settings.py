import os

APP_ID = os.environ.get('FIR_OAUTH_APP_ID', None)
APP_SECRET = os.environ.get('FIR_OAUTH_APP_SECRET', None)
REDIRECT = os.environ.get('FIR_OAUTH_REDIRECT', None)
AUTH_URL = os.environ.get('FIR_OAUTH_AUTH_URL', None)
