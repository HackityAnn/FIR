import requests
import json

graph_url = 'https://graph.microsoft.com/v1.0'

def get_user(token):
    # Get the user information
    headers = {'Authorization': f'Bearer {token}'}
    params = {'$select': 'displayName,mail,mailboxSettings,userPrincipalName'}
    user = requests.get(f'{graph_url}/me', headers=headers, params=params)
    return user.json()