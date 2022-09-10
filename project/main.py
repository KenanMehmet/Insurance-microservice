import logging
import sys

import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from flask import Flask
from flask_restful import Api

from .subscriber import start_rabbitmq_listener
from .commands import cronbp
from .database import startup_migrate
from .views import home, ClientList, Client, PolicyList, Policy

__all__ = ("create_app", "create_worker")

def create_app():
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    
    sentry_sdk.init(
        dsn="https://e85fb4154b6146c5b7bbd0f8cc86959e@o309925.ingest.sentry.io/5872491",
        integrations=[FlaskIntegration()],

        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for performance monitoring.
        # We recommend adjusting this value in production.
        traces_sample_rate=1.0
    )

    startup_migrate()
    app = Flask(__name__)
    app.config.from_pyfile('settings.py')
    api = Api(app)

    # Register HTML routes
    app.add_url_rule('/', view_func=home)

    # Register API Routes
    api.add_resource(ClientList, '/clients')
    api.add_resource(Client, '/clients/<int:carer_id>')
    api.add_resource(PolicyList, '/policies')
    api.add_resource(Policy, '/policies/<int:carer_id>/<string:policy_start_date>')

    # Register Cron Commands
    app.register_blueprint(cronbp)

    return app

def create_worker(app):
    start_rabbitmq_listener()
    #start_kubemq_listener(app.config.get('KUBEMQ_ENV'), app.config.get('KUBEMQ_HOST'), app.config.get('KUBEMQ_PORT'))
