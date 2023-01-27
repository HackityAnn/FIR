from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from fir_ms_oauth2.ms_oauth_helper import get_sign_in_flow, get_token_from_code, store_user, remove_user_and_token
from fir_ms_oauth2.ms_graph_helper import get_user


def home(request):
    context = initialize_context(request)
    return render(request, 'fir_ms_oauth2/home.html', context)


def initialize_context(request):
    context = {'user': request.session.get(
        'user', None), 'token_cache': request.session.get('token_cache', None)}
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

    # Store the user with the helper script
    store_user(request, user)
    return HttpResponseRedirect(reverse('fir_ms_oauth2:home'))
