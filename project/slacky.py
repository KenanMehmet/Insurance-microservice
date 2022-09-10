from slack import WebClient
from .settings import SLACK_TOKEN, FLASK_DEBUG
import requests
import json

sc = WebClient(SLACK_TOKEN)

def send_slack_message(message, channel='helper_site_logging'):
    if FLASK_DEBUG:
        print("slack_dev_sent")
        return True
    payload = {'text': message, 'channel': channel, 'username': 'Insurance Bot',
               'icon_url': 'https://d3amx7e3980juq.cloudfront.net/static/img/new_log.png'}
    url = 'dummy' # Url will be the channel that the message will be sent to
    headers = {'Content-type': 'application/json'}
    send_message = requests.post(
        url,
        headers=headers,
        data=json.dumps(payload)
    )
    if send_message.status_code == 200:
        return True
    return send_message
