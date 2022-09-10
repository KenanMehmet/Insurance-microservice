from os import environ, getenv

# Flask Config
FLASK_DEBUG = (getenv('FLASK_DEBUG', 'False') == 'True')
PREFERRED_URL_SCHEME = environ.get('PREFERRED_URL_SCHEME')
TESTING = (getenv('TESTING', 'False') == 'True')

# Dynamodb
DYNAMODB_ENDPOINT = environ.get('DYNAMODB_ENDPOINT', None)

# KubeMQ
KUBEMQ_ENV = environ.get('KUBEMQ_ENV')
KUBEMQ_HOST = environ.get('KUBEMQ_HOST')
KUBEMQ_PORT = environ.get('KUBEMQ_PORT')

# Core API
CORE_ENDPOINT = environ.get('CORE_ENDPOINT')
CORE_API_KEY = environ.get('CORE_KEY')

# Slack
SLACK_TOKEN = environ.get('SLACK_TOKEN')

# Payment
PAYMENT_NUM = environ.get('PAYMENT_NUM')
PAYMENT_EXP = environ.get('PAYMENT_EXP')
PAYMENT_CVC = environ.get('PAYMENT_CVC')

# SUREWISE
SUREWISE_LOG = environ.get('SUREWISE_LOG')
SUREWISE_PAS = environ.get('SUREWISE_PAS')

# AWS
AWS_REGION = environ.get('AWS_REGION')
AWS_KEY = environ.get('AWS_KEY')
AWS_SECRET = environ.get('AWS_SECRET')

RABBIT_URL = environ.get('RABBIT_URL')
RABBIT_ENV = environ.get('RABBIT_ENV')
RABBIT_USERNAME = environ.get('RABBIT_USERNAME')
RABBIT_PASSWORD = environ.get('RABBIT_PASSWORD')

QUEUE_NAME = 'ms-insurance'