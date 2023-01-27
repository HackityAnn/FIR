import requests

graph_url = 'https://graph.microsoft.com/v1.0'

def get_user(token):
    # Get the user information
    headers = {'Authorization': f'Bearer {token}'}
    params = {'$select': 'userPrincipalName'}
    user = requests.get(f'{graph_url}/me', headers=headers, params=params)
    return user.json()