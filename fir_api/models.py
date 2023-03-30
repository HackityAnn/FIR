"""
Models for the API implementation
"""
from django.db import models

class Oauth2API(models.Model):
    """
    Model for OAuth2 integration for APIs
    the configuration items in this model can be used
    for the token validations
    Primary key for this is the APP_ID of the implemented
    client app id
    """
    app_id = models.CharField(
        max_length=512,
        primary_key=True,
        help_text='The application id of the client app registration that creates the JWT')
    jwks_uri = models.CharField(
        max_length=512,
        help_text='The JWKS URI')
    aud = models.CharField(
        max_length=512,
        help_text='The audience to check for normally it would be the Application ID URI')
    iss = models.CharField(
        max_length=512,
        help_text='The issuer normally https://sts.windows.net/{tenant id}/')
