import json
import requests
import base64
import msal
from django.contrib.auth import login, logout
from django.contrib.auth.models import User, Group
from django.conf import settings
from incidents.models import Profile, IncidentTemplate, Incident, BusinessLine, AccessControlEntry

# Load the oauth settings
oauth_settings = {
    'scopes': [],
    'app_id': settings.APP_ID,
    'app_secret': settings.APP_SECRET,
    'redirect': settings.REDIRECT,
    'auth_url': settings.AUTH_URL
}


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
    # Add the maximum base64 padding just to make sure you never get
    # an padding error
    payload = json.loads(base64.b64decode(role_part_of_token+'=='))
    return payload['roles']

def set_permissions(user: User, token: str, user_businessline: list) -> None:
    roles = get_roles_from_token(token=token)
    user.groups.clear()
    user.user_permissions.clear()
    user.set_unusable_password()
    user.is_superuser = False
    user.is_staff = False
    for role in roles:
        if role == 'FIR.admin':
            user.is_superuser = True
            user.is_staff = True
        if role.startswith('FIR.entity'):
            try:
                businessline = BusinessLine.objects.get(name=user_businessline)
                access_control_role = Group.objects.get(name=role)
                access_control = AccessControlEntry()
                access_control.user = user
                access_control.business_line = businessline
                access_control.role = access_control_role
                access_control.save()
            except BusinessLine.DoesNotExist:
                pass
            except Group.DoesNotExist:
                pass
        else:
            try:
                group = Group.objects.get(name=role)
                user.groups.add(group)
            except Group.DoesNotExist:
                pass
    user.save()
    return

def get_businessline_from_graph_api(token: str) -> str:
    graph_url_me = 'https://graph.microsoft.com/v1.0/me'
    headers = {'Authorization': f'Bearer {token}'}
    params = {'$select': 'companyName'}
    businessline = requests.get(graph_url_me, headers=headers, params=params).json()['companyName']
    return businessline

def initialize_session(request, user, user_businessline):
    # Put all the incident templates in the session
    request.session['incident_templates'] = list(IncidentTemplate.objects.exclude(name='default').values('name'))
    request.session['has_incident_templates'] = len(request.session['incident_templates']) > 0
    request.session['can_report_event'] = user.has_perm('incidents.handle_incidents', obj=Incident) or \
                                          user.has_perm('incidents.report_events', obj=Incident)
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
    access_token_dict = json.loads(request.session.get('token_cache'))['AccessToken']
    access_user_key = next(iter(access_token_dict))
    access_token = access_token_dict[access_user_key]['secret']
    user_businessline = get_businessline_from_graph_api(access_token)
    set_permissions(user, id_token, user_businessline)
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
