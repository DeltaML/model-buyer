from google.auth.transport import requests
from google.oauth2 import id_token
import logging


class UserLoginService:
    """
    Use:
    https://developers.google.com/identity/sign-in/web/backend-auth
    """

    CLIENT_ID = "334168139568-v83065ekhqqkd4ieppo2jjb4aqbdk5o8.apps.googleusercontent.com"

    @staticmethod
    def validate(idinfo):
        return idinfo['iss'] in ['accounts.google.com', 'https://accounts.google.com']


    @staticmethod
    def get_user_info(token):
        idinfo = id_token.verify_oauth2_token(token, requests.Request(), UserLoginService.CLIENT_ID)
        logging.info(idinfo)
        return idinfo

