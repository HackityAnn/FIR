from django.urls import re_path

from fir_ms_oauth2 import views

app_name = 'fir_ms_oauth2'

urlpatterns = [
    re_path(r'^sign_in', views.sign_in, name='sign_in'),
    re_path(r'^sign_out', views.sign_out, name='sign_out'),
    re_path(r'^redirect', views.redirect, name='redirect'),
]
