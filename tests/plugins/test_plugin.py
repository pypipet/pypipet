import pytest
from pipet.plugins.paypal.app import *
from pprint import pprint


def test_paypal():
    client_id= ''
    secret=''
    url = 'https://api-m.paypal.com/'
    api = get_api(url, client_id, secret)
    print(f'connection {api.error is None}')