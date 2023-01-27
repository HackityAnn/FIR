from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from fir_ms_oauth2.ms_oauth_helper import get_sign_in_flow, get_token_from_code, store_user, remove_user_and_token, store_groups, store_token
from fir_ms_oauth2.ms_graph_helper import get_user, get_groups

def home(request):
    context = initialize_context(request)
    return render(request, 'fir_ms_oauth2/home.html', context)

def initialize_context(request):
    context = {'user': request.session.get('user', None), 'groups': request.session.get('groups', None), 'token': request.session.get('token', None)}
    return context

def sign_in(request):
    # Get the sign in flow
    flow = get_sign_in_flow()
    # Save the flow to use in the redirect
    request.session['auth_flow'] = flow
    return HttpResponseRedirect(flow['auth_uri'])

def sign_out(request):
    # Clear token and user
    remove_user_and_token(request)
    return HttpResponseRedirect(reverse('fir_ms_oauth2:home'))

def redirect(request):
    # Make the token request
    result = get_token_from_code(request)

    # Get the user's profile from graph API
    user = get_user(result['access_token'])
    groups = get_groups(result['access_token'])

    # Store the user with the helper script
    store_user(request, user)
    store_groups(request, groups)
    store_token(request, result['access_token'])
    return HttpResponseRedirect(reverse('fir_ms_oauth2:home'))
