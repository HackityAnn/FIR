from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from fir_ms_oauth2.ms_oauth_helper import get_sign_in_flow, remove_user_and_token, get_token_from_code, get_user_from_request
from incidents.views import log


def sign_in(request):
    # Get the sign in flow
    flow = get_sign_in_flow()
    # Save the flow to use in the redirect
    request.session['auth_flow'] = flow
    return HttpResponseRedirect(flow['auth_uri'])


def sign_out(request):
    # Clear token and user
    log(f'Logout initiated for SSO user: {request.user.username}', user=request.user)
    remove_user_and_token(request)
    return HttpResponseRedirect('/')


def redirect(request):
    get_token_from_code(request)
    get_user_from_request(request)
    log(f'Login success for SSO user: {request.user.username}', user=request.user)
    return HttpResponseRedirect('/')
