import binascii,os
import shopify
from urllib.parse import urlparse
from urllib.parse import parse_qs

def get_auth_url(API_KEY, API_SECRET, shop_url,  scopes, redirect_uri, **kwargs):
    shopify.Session.setup(api_key=API_KEY, secret=API_SECRET)
    state = kwargs.get('state', binascii.b2a_hex(os.urandom(15)).decode("utf-8"))
    api_version = kwargs.get('api_version','2020-10')

    session = shopify.Session(shop_url, api_version)
    return session.create_permission_url(scopes, redirect_uri, state)

def get_acess_token(shop_url, target_url, **kwargs):
    api_version = kwargs.get('api_version','2020-10')
    session = shopify.Session(shop_url, api_version)
    params = _parse_target_url(target_url)
    return session.request_token(params) 

def start_session(private_app=True, **kwargs):
    api_version = kwargs.get('api_version','2020-10')
    if private_app:
        return shopify.Session(kwargs['shop_url'], api_version, 
                      kwargs['private_app_password'])
    else:
        return shopify.Session(kwargs['shop_url'], api_version, 
                    kwargs['access_token'])

def _parse_target_url(url):
    parsed_url = urlparse(url)
    params = parse_qs(parsed_url.query)
    for key, value in params.items():
        params[key] = value[0]
    return params