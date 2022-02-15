from requests import request
from json import dumps as jsonencode
from time import time
from pypipet.plugins.woocommerce.oauth import OAuth
from requests.auth import HTTPBasicAuth
from urllib.parse import urlencode
from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session
from oauthlib.common import urlencode
import base64, time

def encode_base64(text):
    return  base64.b64encode(bytes(text, 'utf-8'))

class API(object):
    """ API Class """

    def __init__(self, url, client_id, secret, **kwargs):
        self.error = None
        if url.endswith("/") is False:
            self.url = f"{url}/"
        else:
            self.url = url
        self._AUTH_URL =  kwargs.get("auth_url", "v1/oauth2/token")
        self.client_id = client_id
        self.secret = secret
        self.version = kwargs.get("version", "v1")
        self.is_ssl = self.__is_ssl()
        self.timeout = kwargs.get("timeout", 800)
        self.verify_ssl = kwargs.get("verify_ssl", True)
        self.__get_oauth_token(self._AUTH_URL)
        

    def __is_ssl(self):
        """ Check if url use HTTPS """
        return self.url.startswith("https")

    def __get_url(self, endpoint):
        """ Get URL for requests """
        return f"{self.url}{self.version}/{endpoint}"

    def __get_oauth_token(self, endpoint,  **kwargs):
        auth =HTTPBasicAuth(self.client_id, self.secret)
        client = BackendApplicationClient(client_id=self.client_id)
        oauth = OAuth2Session(client=client)
        url = f"{self.url}{endpoint}"
        try:
            token = oauth.fetch_token(token_url=url, 
                                    client_id=encode_base64(self.client_id),
                                    client_secret=encode_base64(self.secret), 
                                    auth=auth)
            self.token = token['access_token']
            self.expire_at = token['expires_at']
        except:
            self.error = 'oauth failed'
        

    def __request(self, method, endpoint, data, params=None, **kwargs):
        """ Do requests """

        #check if token expired
        if time.time() > self.expire_at:
            self.__get_oauth_token(self._AUTH_URL)

        if params is None:
            params = {}
        url = self.__get_url(endpoint)
        auth = None
        headers = {
            "Authorization": f"Bearer {self.token}",
            "accept": "application/json"
        }


        if data is not None:
            data = jsonencode(data, ensure_ascii=False).encode('utf-8')
            headers["content-type"] = "application/json;charset=utf-8"
        return request(
            method=method,
            url=url,
            verify=self.verify_ssl,
            auth=auth,
            params=params,
            data=data,
            timeout=self.timeout,
            headers=headers,
            **kwargs
        )

    def get(self, endpoint, **kwargs):
        """ Get requests """
        return self.__request("GET", endpoint, None, **kwargs)

    def post(self, endpoint, data, **kwargs):
        """ POST requests """
        return self.__request("POST", endpoint, data, **kwargs)

    def put(self, endpoint, data, **kwargs):
        """ PUT requests """
        return self.__request("PUT", endpoint, data, **kwargs)

    def delete(self, endpoint, **kwargs):
        """ DELETE requests """
        return self.__request("DELETE", endpoint, None, **kwargs)

    def options(self, endpoint, **kwargs):
        """ OPTIONS requests """
        return self.__request("OPTIONS", endpoint, None, **kwargs)
