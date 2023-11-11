import json
import requests

from common.configs import OXAPAY_MERCHANT


def get_payment_information(track_id):

    url = 'https://api.oxapay.com/merchants/inquiry'
    data = {
        'merchant': OXAPAY_MERCHANT,
        'trackId': track_id
    }

    response = requests.post(url, data=json.dumps(data))

    return response.json()