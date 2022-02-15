from pypipet.plugins.paypal import API
from requests import request
from requests.auth import HTTPBasicAuth


def get_api(url, client_id, secret):
    return API(url, client_id, secret)


def update_tracking(pp_api, tracking_data:list):
    endpoint = f"shipping/trackers-batch"
    res = pp_api.post(endpoint, data={'trackers':tracking_data})
    return res