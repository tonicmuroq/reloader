# coding: utf-8

import requests
from reloader.config import config


def send_sms(message):
    data = {'tos': config.mobiles.split(','), 'content': message}
    return requests.post(config.sms_url, data=data)
