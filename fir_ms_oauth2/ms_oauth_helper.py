import json
import datetime
import msal
from django.contrib.auth.models import User
# Load the oauth settings
with open('fir_ms_oauth2/oauth_settings.json', 'r') as f:
    oauth_settings = json.load(f)


def load_cache(request):
    # Checking for a token cache in the existing session
    cache = msal.SerializableTokenCache()
    if request.session.get('token_cache'):
        cache.deserialize(request.session['token_cache'])
    return cache


def save_cache(request, cache):
    # If cache changes we want to save it back to the session
    if cache.has_state_changed:
        request.session['token_cache'] = cache.serialize()
        request.session.set_expiry(0)


def get_msal_app(cache=None):
    # Initialize the msal client app
    auth_app = msal.ConfidentialClientApplication(
        oauth_settings['app_id'],
        authority=oauth_settings['auth_url'],
        client_credential=oauth_settings['app_secret'],
        token_cache=cache
    )
    return auth_app


def get_sign_in_flow():
    # Method to generate the signin flow
    auth_app = get_msal_app()
    return auth_app.initiate_auth_code_flow(
        oauth_settings['scopes'],
        redirect_uri=oauth_settings['redirect']
    )

def get_token_from_code(request):
    # Method to exchange auth code for an access token
    cache = load_cache(request)
    auth_app = get_msal_app(cache)

    # Get the flow already saved in the session
    flow = request.session.pop('auth_flow', {})
    auth_app.acquire_token_by_auth_code_flow(flow, request.GET)
    save_cache(request, cache)

    return


def store_user(request, user):
    request.session['user'] = str(user)
    return


def get_token(request):
    cache = load_cache(request)
    auth_app = get_msal_app(cache)

    accounts = auth_app.get_accounts()
    if accounts:
        result = auth_app.acquire_token_silent(
            oauth_settings['scopes'],
            account=accounts[0]
        )
        save_cache(request, cache)
        return result['access_token']
    return


def remove_user_and_token(request):
    if 'token_cache' in request.session:
        del request.session['token_cache']
    return
