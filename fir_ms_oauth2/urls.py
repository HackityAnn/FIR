from django.urls import path

from fir_ms_oauth2 import views

app_name = 'fir_ms_oauth2'

urlpatterns = [
    path('ms_auth/home', views.home, name='home'),
    path('ms_auth/signin', views.sign_in, name='signin'),
    path('ms_auth/signout', views.sign_out, name='signout'),
    path('ms_auth/redirect', views.redirect, name='redirect'),
]

