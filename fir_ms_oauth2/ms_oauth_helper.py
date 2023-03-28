import json
import requests
import base64
import msal
from django.contrib.auth import login, logout
from django.contrib.auth.models import User, Group
from incidents.models import Profile, IncidentTemplate, Incident
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

def get_roles_from_token(token: str) -> list:
    role_part_of_token = token.split('.')[1]
    payload = json.loads(base64.b64decode(role_part_of_token))
    return payload['roles']

def set_permissions(user: User, token: str) -> None:
    roles = get_roles_from_token(token=token)
    user.groups.clear()
    user.user_permissions.clear()
    user.is_superuser = False
    for role in roles:
        if role == 'FIR.admin':
            user.is_superuser = True
        else:
            try:
                group = Group.objects.get(name=role)
                user.groups.add(group)
            except Group.DoesNotExist:
                pass
    user.save()
    return

def get_businessline_from_graph_api(token: str):
    graph_url_me = 'https://graph.microsoft.com/v1.0/me'
    headers = {'Authorization': f'Bearer {token}'}
    user = requests.get(graph_url_me, headers=headers).json()
    return user

def initialize_session(request, user, user_businessline):
    # Put all the incident templates in the session
    request.session['incident_templates'] = list(IncidentTemplate.objects.exclude(name='default').values('name'))
    request.session['has_incident_templates'] = len(request.session['incident_templates']) > 0
    request.session['can_report_event'] = user.has_perm('incidents.handle_incidents', obj=Incident) or \
                                          user.has_perm('incidents.report_events', obj=Incident)
    if user.objects.filter(groups_name_in=['FIR.entity', 'FIR.entity_read_only']):
        request.session['user_businessline'] = user_businessline
    return

def get_user_from_request(request):
    account = json.loads(request.session.get('token_cache'))['Account']
    user_key = next(iter(account))
    ms_home_account_id = account[user_key]['home_account_id']
    try:
        profile = Profile.objects.get(ms_home_account_id=ms_home_account_id)
        user = profile.user
    except Profile.DoesNotExist:
        username = account[user_key]['username']
        user = User.objects.create_user(username)
        user.set_unusable_password()
        user.save()
        profile = Profile()
        profile.user = user
        profile.ms_home_account_id = ms_home_account_id
        profile.hide_closed = False
        profile.incident_number = 50
        profile.save()

    id_token_dict = json.loads(request.session.get('token_cache'))['IdToken']
    id_user_key = next(iter(id_token_dict))
    id_token = id_token_dict[id_user_key]['secret']
    set_permissions(user, id_token)
    user_businessline = get_businessline_from_graph_api(id_token)
    initialize_session(request, user, user_businessline)

    if user.is_active:
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')

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
    logout(request)
    return
