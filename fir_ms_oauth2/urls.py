from django.urls import re_path

from fir_ms_oauth2 import views

app_name = 'fir_ms_oauth2'

urlpatterns = [
    re_path(r'^home', views.home, name='home'),
    re_path(r'^signin', views.sign_in, name='signin'),
    re_path(r'^signout', views.sign_out, name='signout'),
    re_path(r'^redirect', views.redirect, name='redirect'),
]

