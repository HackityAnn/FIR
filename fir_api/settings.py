# REST framework settings
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': ('rest_framework.permissions.IsAuthenticated',),
    # if you prefer to use default TokenAuthentication using Basic Auth mechanism, 
    # replace fir_api.authentication.TokenAuthentication with rest_framework.authentication.TokenAuthentication
    # and delete the OAuth2JWTAuthentication
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'fir_api.authentication.OAuth2JWTAuthentication',
        'fir_api.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication'
        ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    'PAGE_SIZE': 25,
    # Following configuration is dedicated to fir_api.authentication.TokenAuthentication
    # so not for the OAuth2JWTAuthentication
    'TOKEN_AUTHENTICATION_KEYWORD': 'Token',
    'TOKEN_AUTHENTICATION_META': 'HTTP_X_API', # HTTP_X_API == X-Api in headers
}
