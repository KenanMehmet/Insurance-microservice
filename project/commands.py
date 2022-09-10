import requests
import json
import logging
from .database import (delete_last_month_visits, get_uninsured_clients, get_insured_clients, add_policy, update_client_insurance,
                    get_next_month_visits, get_tomorrow_visits, cancel_policy, delete_last_month_visits, get_most_recent_policy, update_policy)
from .webdriver import log_in, cancel_quote, request_quote
from flask import Blueprint
from datetime import datetime, timezone
from dateutil import relativedelta
from .utils import get_end_of_a_month

from .slacky import send_slack_message

cronbp = Blueprint('cron', __name__)
cronbp.config = {}

@cronbp.record
def record_params(setup_state):
    app = setup_state.app
    cronbp.config = dict([(key, value)
                          for (key, value) in app.config.items()])


@cronbp.cli.command('daily')
def daily(): # This command will be run once a day to insure clients with visits
    clients = get_uninsured_clients()
    driver = log_in()
    client = clients[0] # this is used to only run through one client.
    #for client in clients:
    if client:
        url = "%s/api/clients/%s" % (
            cronbp.config.get('CORE_ENDPOINT'),
            client['client_id'],
        )
        payload = {}
        headers = {
            'Authorization': 'Basic %s' % cronbp.config.get('CORE_API_KEY')
            }
        response = requests.request("GET", url, headers=headers, data=payload)
        my_json = json.loads(response.text)
        if not 'detail' in my_json: # Detail will appear in the json if the client_id has no details on our core database
            visits = get_tomorrow_visits(client['client_id'])
            if visits['Count'] > 0: #If they have a visit tomorrow then we will insure them
                policy_no = request_quote(driver, my_json)
                if policy_no: # If the request quote function is successful it will return a policy_no
                    add_policy(client['client_id'], policy_no)
                    update_client_insurance(client['client_id'], get_end_of_a_month(datetime.now(), 1), True)
                    send_slack_message("Daily Insured: Client ID: %s successful" % client['client_id'])
                else: # Otherwise it will return false
                    send_slack_message("Could not insure client id %s please investigate" % client['client_id'])
        else:
            send_slack_message("Could not find client id %s, please investigate" % client['client_id'])
    driver.quit()
    send_slack_message("Finished daily insurance")


@cronbp.cli.command('monthly')
def monthly(): # Runs through at the end of the month to check which insured clients we want to uninsure.
    clients = get_insured_clients()
    driver = log_in()
    for client in clients:
        visits = get_next_month_visits(client['client_id'])
        if visits['Count'] > 0: #If the client has visits next month we will want to reinsure them.
            update_policy(client['client_id']) # If client has upcoming visits, we want to change their policy end date to next month
            send_slack_message("Monthly Insurance: Client ID %s policy end date extended to next month" % client['client_id'])
        else: #otherwise we want to uninsure them
            policy_no = get_most_recent_policy()
            cancel_quote(driver, policy_no['policy_number']) # Runs through webdriver for canceling a quote
            cancel_policy(client['client_id'], policy_no['policy_start_date']) # Sets the policy end_date to midnight and changes client insurance to uninsured
            send_slack_message("Montly Insurance: Client ID %s is now uninsured" % client['client_id'])
    delete_last_month_visits() # We then want to delete all visits past today as we do not need that data anymore on this microservice
    driver.quit()
    send_slack_message("Finished monthly insurance")
