"""
Authentication classes for API authentication
Has token and OAuth2JWT authentication classes
"""
from typing import Tuple
import jwt
from jwt import PyJWKClient
import jwt.exceptions as jexcept
from rest_framework import authentication, exceptions
from rest_framework.settings import api_settings
from fir_api.models import Oauth2API
from incidents.models import User

class TokenAuthentication(authentication.TokenAuthentication):
    """
    Simple token based authentication.
    Clients should authenticate by passing the token key in the "Authorization"
    HTTP header, prepended with the string "Token ".  For example:
        X-Api: Token 401f7ac837da42b97f613d789819ff93537bee6a
    """

    keyword = api_settings.user_settings['TOKEN_AUTHENTICATION_KEYWORD']

    def authenticate(self, request):
        meta = api_settings.user_settings['TOKEN_AUTHENTICATION_META']
        auth = request.META.get(meta)        
        if not auth:
            return None
        try:
            auth_keyword, auth_token = auth.split(' ')
        except ValueError:
            msg = "Invalid token header. Header must be defined the following way: 'Token hexstring'"
            raise exceptions.AuthenticationFailed(msg)
        if auth_keyword.lower() != self.keyword.lower():
            msg = f"Provided keyword '{auth_keyword.lower()}' does not match defined one '{self.keyword.lower()}'"
            raise exceptions.AuthenticationFailed(msg)
        return self.authenticate_credentials(auth_token)

class OAuth2JWTAuthentication(authentication.BaseAuthentication):
    """
    JWT authentication focussed and tested on implementation
    with Azure AD
    """

    def __init__(self):
        """
        Init a list of expected exceptions for JWT
        validation
        """
        self.jwt_validation_exceptions = (
            jexcept.DecodeError,
            jexcept.InvalidSignatureError,
            jexcept.ExpiredSignatureError,
            jexcept.InvalidAudienceError,
            jexcept.InvalidIssuerError,
            jexcept.InvalidIssuedAtError,
            jexcept.ImmatureSignatureError,
        )

    def validate_token(self, token: str) -> list:
        """
        Validates the JWT

        Args:
            token (str): JWT (from Azure AD)

        Raises:
            exceptions.AuthenticationFailed: When failing to validate or decode the token

        Returns:
            list: the roles from the token (should only be one)
        """
        try:
            token_app_id = jwt.decode(token, options={'verify_signature': False})['appid']
        except jwt.exceptions.InvalidTokenError:
            msg = 'JWT received is invalid and cannot be decoded'
            raise exceptions.AuthenticationFailed(msg)
        try:
            app_id_configuration = Oauth2API.objects.get(app_id=token_app_id)
        except Oauth2API.DoesNotExist:
            msg = f'App ID: {token_app_id} is not configured on the backend yet'
            raise exceptions.AuthenticationFailed(msg)
        jwks_client = PyJWKClient(app_id_configuration.jwks_uri)
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        verification = {
            'verify_signature': True,
            'require': ['aud', 'iss', 'iat', 'exp', 'nbf'],
            'verify_aud': 'verify_signature',
            'verify_iss': 'verify_signature',
            'verify_iat': 'verify_signature',
            'verify_exp': 'verify_signature',
            'verify_nbf': 'verify_signature'
        }
        try:
            payload = jwt.decode(token,
                                key=signing_key.key,
                                algorithms=['RS256'],
                                audience=app_id_configuration.aud,
                                issuer=app_id_configuration.iss,
                                options=verification)
        except self.jwt_validation_exceptions as e:
            msg = f'Failed to validate JWT with exception {e.args[0]}'
            raise exceptions.AuthenticationFailed(msg)
        return payload['roles']

    def get_user_from_role(self, role: list) -> User:
        """
        gets the user from the role
        the role needs to be the username

        Args:
            role (list): the role list (max 1)

        Raises:
            exceptions.AuthenticationFailed: if user doesn't exist or isn't active we fail 
                                            the authentication 

        Returns:
            User: user from incidents User model
        """
        try:
            user = User.objects.get(username=role[0])
        except User.DoesNotExist:
            msg = 'Role does not exist, create a user in the backend first'
            raise exceptions.AuthenticationFailed(msg)
        if not user.is_active:
            msg = 'User is not active'
            raise exceptions.AuthenticationFailed(msg)
        return user

    def authenticate(self, request) -> Tuple[User, None]:
        """
        Validate the token and get the user from
        the roles part of the token (Microsoft JWT)

        Args:
            request (_type_): Django request object

        Raises:
            exceptions.AuthenticationFailed: Any errors raise a failed authentication

        Returns:
            Tuple[User, None]: returns a tuple with a user object and None for auth object
        """
        auth = request.headers.get('Authorization')
        if not auth:
            return None
        try:
            prefix, received_token = auth.split(' ')
        except ValueError:
            msg = 'Invalid token header. Header must be defined as: "Bearer base64token"'
            raise exceptions.AuthenticationFailed(msg)
        if prefix.lower() != 'bearer':
            msg = f'Provided keyword {prefix} does not match the defined one Bearer'
            raise exceptions.AuthenticationFailed(msg)
        role = self.validate_token(token=received_token)
        if not role:
            msg = 'No role has been added to the token'
            raise exceptions.AuthenticationFailed(msg)
        if len(role) > 1:
            msg = 'Multiple roles added to token, while only one is allowed roles:{role}'
            raise exceptions.AuthenticationFailed(msg)

        user = self.get_user_from_role(role=role)
        return user, None
