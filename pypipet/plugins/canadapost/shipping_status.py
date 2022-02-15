import requests



def request_handler(func):
    def wrapper(*args, **kwargs):
        try:
            res = func(*args, **kwargs)
            if res.status_code in [200, 201]:
                return res.json()
            logger.debug(res.json())
            return None
        except  KeyError as e:
            logger.debug('requst error')
            logger.debug(e)
    return wrapper


@request_handler
def get_status(tracking_id):
    domain = "https://www.canadapost-postescanada.ca"
    return requests.get(f"{domain}/track-reperage/rs/track/json/package/{tracking_id}/detail")