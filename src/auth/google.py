import streamlit as st
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
import requests
from src.configs import env



def get_authorization_url():
    return (
        f"https://accounts.google.com/o/oauth2/auth?response_type=code"
        f"&client_id={env.CLIENT_ID}"
        f"&redirect_uri={env.REDIRECT_URI}"
        f"&scope=openid%20email%20profile"
        f"&state=security_token"
        f"&prompt=consent"
    )


def get_token_from_code(auth_code):
    try :
        token_request_uri = 'https://oauth2.googleapis.com/token'
        token_request_data = {
        'code': auth_code,
        'client_id': env.CLIENT_ID,
        'client_secret': env.CLIENT_SECRET,
        'redirect_uri': env.REDIRECT_URI,
        'grant_type': 'authorization_code'
        }
        token_response = requests.post(token_request_uri, data=token_request_data)

        if token_response.status_code != 200:
           st.write(f"Failed to get token: {token_response.text}")
           return None

        token_json = token_response.json()
        return token_json.get('id_token')
    except Exception as e:
        st.error(f'An error occurred while execution of function get_token_from_code() => : {e}')


def verify_id_token(token):
    try:
        idinfo = id_token.verify_oauth2_token(token, google_requests.Request(),clock_skew_in_seconds=10)
        if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            raise ValueError('Wrong issuer.')
        return idinfo
    except ValueError as e:
        st.write(f"Token verification failed: {e}")
        return None

