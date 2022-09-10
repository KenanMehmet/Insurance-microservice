import boto3
from boto3.dynamodb.conditions import Key, Attr
from datetime import datetime, timedelta, timezone
from botocore.exceptions import ClientError
from dateutil import relativedelta
import json
import logging
from .settings import DYNAMODB_ENDPOINT, AWS_REGION, AWS_KEY, AWS_SECRET
from .utils import convert_to_utc, get_midnight, get_end_of_a_month

if not DYNAMODB_ENDPOINT:
    ddb = boto3.resource('dynamodb',
                    region_name=AWS_REGION)
else:
    ddb = boto3.resource('dynamodb',
        endpoint_url=DYNAMODB_ENDPOINT,
        aws_access_key_id=AWS_KEY,
        aws_secret_access_key=AWS_SECRET,
        region_name=AWS_REGION)

def create_table(name, schema, definitions):
    try:
        table = ddb.create_table(
            TableName=name,
            KeySchema=schema,
            AttributeDefinitions=definitions,
            ProvisionedThroughput={
                'ReadCapacityUnits': 3,
                'WriteCapacityUnits': 3,
            }
        )
        logging.info(table)
    except ClientError as e:
        if e.response['Error']['Code'] == "ResourceInUseException":
            logging.info("TABLE %s: Exists" % name)
        else:
            logging.info('TABLE %s: Error' % name)
            logging.info(e)


def startup_migrate():
    logging.info("DERKJHFDJH")
    create_table(
        'visits',
        [
            {'AttributeName': 'client_id', 'KeyType': 'HASH'},
            {'AttributeName': 'start_time', 'KeyType': 'RANGE'}
        ],
        [
            {'AttributeName': 'client_id', 'AttributeType': 'S'},
            {'AttributeName': 'start_time', 'AttributeType': 'S'}
        ],
    )
    create_table(
        'clients',
        [
            {'AttributeName': 'client_id', 'KeyType': 'HASH'},
        ],
        [
            {'AttributeName': 'client_id', 'AttributeType': 'S'},
        ],
    )
    create_table(
        'policies',
        [
            {'AttributeName': 'client_id', 'KeyType': 'HASH'},
            {'AttributeName': 'policy_start_date', 'KeyType': 'RANGE'}
        ],
        [
            {'AttributeName': 'client_id', 'AttributeType': 'S'},
            {'AttributeName': 'policy_start_date', 'AttributeType': 'S'}
        ],
    )


def handle_accept_visit(input):
    try:
        add_visit(input['client_id'], input['id'], input['start_time'], input['end_time'])
    except ClientError as e:
        if e.response['Error']['Code'] == "TransactionCanceledException":
            logging.info(e.response['Error']['Message'])
            return
        else:
            raise
    try:
        add_client(input)
    except ClientError as e:
        if e.response['Error']['Code'] == "TransactionCanceledException":
            client = get_client(input['client_id'])
            insured_end_date = datetime.strptime(client['insured_end_date'], '%Y-%m-%d %H:%M:%S')
            visit_eom = get_end_of_a_month(convert_to_utc(input['start_time']), 1)
            if insured_end_date < visit_eom:
                update_client_insurance(input['client_id'], visit_eom, client['insured'])
                logging.info("Client ID: %s insured end date updated to %s" % (input['client_id'], visit_eom))
        else:
            raise


def handle_delete_visit(input):
    table = ddb.Table('visits')
    visits = table.query(
        ScanIndexForward=False,
        KeyConditionExpression=Key('client_id').eq(str(input['client_id']))
        )
    items = visits['Items']
    if visits['Count'] > 0:
        if len(items) > 1:
            last = items[0]
            start_time = convert_to_utc(input['start_time'])
            if last['start_time'] == start_time:
                second_last = items[1]
                second_last_date = datetime.strptime(second_last['start_time'],'%Y-%m-%d %H:%M:%S')
                second_last_eom = get_end_of_a_month(second_last_date, 1)
                client = get_client(input['client_id'])
                insured_end_date = client['insured_end_date']
                insured_end_date = datetime.strptime(insured_end_date,'%Y-%m-%d %H:%M:%S')
                if insured_end_date != second_last_eom:
                    update_client_insurance(input['client_id'], second_last_eom, client['insured'])
                    logging.info("Client ID: %s insured end date updated to %s" % (input['client_id'], second_last_eom))
        try:
            delete_visit(input['client_id'], input['start_time'], input['id'])
        except ClientError as e:
            if e.response['Error']['Code'] == "TransactionCanceledException":
                logging.info(e.response['Error']['Message'])
                return
            else:
                raise
        else:
            logging.info("item deleted")
            if len(items) <= 1:
                client = get_client(input['client_id'])
                end_of_month = get_end_of_a_month(datetime.now(), 1)
                update_client_insurance(input['client_id'], str(end_of_month), client['insured'])
                logging.info("Client ID: %s insured end date updated to %s" % (input['client_id'], end_of_month))
    else:
        logging.info("No visits found for Client id: %s" % (input['client_id']))

def add_visit(client_id: int, visit_id: int, start_time: str, end_time: str):
    start_time = convert_to_utc(start_time)
    response = ddb.meta.client.transact_write_items(
        TransactItems=[
            {
                'Put': {
                    'Item': {
                        'client_id': str(client_id),
                        'start_time': str(start_time),
                        'visit_id': str(visit_id),
                        'end_time': str(end_time,)
                    },
                    'TableName': 'visits',
                    "ConditionExpression": "attribute_not_exists(client_id) AND attribute_not_exists(start_time)",
                }
            },
            {
                'Put': {
                    'Item': {
                        'client_id': ('visit_id#%s' % visit_id),
                        'start_time': str(start_time)
                    },
                    'TableName': 'visits',
                    "ConditionExpression": "attribute_not_exists(client_id)",
                }
            }
        ]
    )

def add_client(input):
    end_of_month = get_end_of_a_month(datetime.now(), 1)
    response = ddb.meta.client.transact_write_items(
        TransactItems=[
            {
                'Put': {
                    'Item': {
                        'client_id': str(input['client_id']),
                        'insured': False,
                        'insured_end_date': str(end_of_month)
                    },
                    'TableName': 'clients',
                    "ConditionExpression": "attribute_not_exists(client_id)",
                }
            }
        ]
    )

def delete_visit(client_id: int, start_time_string: str, visit_id: int):
    start_time = convert_to_utc(start_time_string)
    response = ddb.meta.client.transact_write_items(
        TransactItems=[
            {
                'Delete': {
                    'Key': {
                        'client_id': str(client_id),
                        'start_time': str(start_time)
                    },
                    'TableName': 'visits',
                }
            },
            {
                'Delete': {
                    'Key': {
                        'client_id': ('visit_id#%s' % visit_id),
                        'start_time': str(start_time)
                    },
                    'TableName': 'visits',
                }
            }
        ]
    )

def delete_last_month_visits():
    midnight = get_midnight(datetime.now())
    table = ddb.Table('visits')
    scan = table.scan(
        FilterExpression = Key('start_time').lte(str(midnight))
    )
    with table.batch_writer() as batch:
        for each in scan['Items']:
            batch.delete_item(
                Key={
                    'client_id': each['client_id'],
                    'start_time': each['start_time']
                }
            )

def get_uninsured_clients():
    table = ddb.Table('clients')
    response = table.scan(
        FilterExpression = Attr('insured').eq(False)
    )
    return response['Items']

def get_tomorrow_visits(client_id):
    midnight = get_midnight(datetime.now())
    table = ddb.Table('visits')
    response = table.scan(
        Select='COUNT',
        FilterExpression = Key('client_id').eq(str(client_id)) & Key('start_time').gte(str(midnight + timedelta(days=1))) & Key('start_time').lt(str(midnight + timedelta(days=2)))
    )
    return response

def get_next_month_visits(client_id):
    midnight = get_midnight(datetime.now())
    table = ddb.Table('visits')
    response = table.scan(
        Select='COUNT',
        FilterExpression = Key('client_id').eq(str(client_id)) & Key('start_time').gte(str(midnight)) & Key('start_time').lt(str(get_end_of_a_month(datetime.now(), 2))))
    return response

def get_insured_clients():
    table = ddb.Table('clients')
    response = table.scan(
        FilterExpression = Attr('insured').eq(True)
    )
    return response['Items']

def update_client_insurance(client_id, insured_end_date, insured):
    response = ddb.meta.client.transact_write_items(
        TransactItems=[
            {
                'Update': {
                    'Key': {
                        'client_id': str(client_id)
                    },
                    'TableName': 'clients',
                    'UpdateExpression': "set insured_end_date = :d, insured = :t",
                    'ExpressionAttributeValues': {
                        ':d': str(insured_end_date),
                        ':t': insured,
                    },
                }
            }
        ]
    )


def add_policy(client_id, policy_number):
    response = ddb.meta.client.transact_write_items(
        TransactItems=[
            {
                'Put': {
                    'Key': {
                        'client_id': str(client_id),
                        'policy_start_date': str(datetime.now()),
                        'policy_end_date': str(get_end_of_a_month(datetime.now(), 1)),
                        'policy_number': policy_number
                    },
                    'TableName': 'policies',
                    },
            }
        ]
    )

def update_policy(client_id):
    end_of_next_month = get_end_of_a_month(datetime.now(), 1)
    policy = get_most_recent_policy()
    response = ddb.meta.client.transact_write_items(
        TransactItems=[
            {
                'Update': {
                    'Key': {
                        'client_id': client_id,
                        'policy_start_date': policy['policy_start_date']
                    },
                    'TableName': 'policies',
                    'UpdateExpression': "set policy_end_date = :d",
                    'ExpressionAttributeValues': {
                        ':d': end_of_next_month
                    },
                }
            },
        ]
    )

def cancel_policy(client_id, policy):
    midnight = get_midnight(datetime.now())
    response = ddb.meta.client.transact_write_items(
        TransactItems=[
            {
                'Update': {
                    'Key': {
                        'client_id': client_id,
                        'policy_start_date': policy
                    },
                    'TableName': 'policies',
                    'UpdateExpression': "set policy_end_date = :d",
                    'ExpressionAttributeValues': {
                        ':d': midnight
                    },
                }
            },
            {
                'Update': {
                    'Key': {
                        'client_id': client_id
                    },
                    'TableName': 'clients',
                    'UpdateExpression': "set insured_end_date = :d, insured = :t",
                    'ExpressionAttributeValues': {
                        ':d': midnight,
                        ':t': False
                    },
                }
            }
        ]
    )

def get_most_recent_policy(client_id):
    table = ddb.Table('policies')
    response = table.query(
        ScanIndexForward = False,
        KeyConditionExpression = Key('client_id').eq(client_id)
    )
    response = response['Items']
    return response[0]

def get_client(id):
    table = ddb.Table('clients')
    response = table.get_item(Key={
        "client_id": str(id),
    })
    if 'Item' in response:
        return response['Item']
    return None

def get_policy(id, policy_start):
    table = ddb.Table('clients')
    response = table.get_item(Key={
        "client_id": str(id),
        "policy_start_date": policy_start
    })
    return response['Item']

def get_paginated_clients(last=None, limit=25):
    table = ddb.Table('clients')
    if last:
        scan = table.scan(
            Limit=limit,
            ExclusiveStartKey={
                'client_id': last
            }
        )
    else:
        scan = table.scan(
            Limit=limit,
        )
    logging.info(scan)
    clients = []
    with table.batch_writer() as batch:
        for each in scan['Items']:
            clients.append(each)

    logging.info(clients)

    return clients

def get_paginated_policies(last=None, limit=25):
    table = ddb.Table('policies')
    if last:
        scan = table.scan(
            Limit=limit,
            ExclusiveStartKey={
                'client_id': last
            }
        )
    else:
        scan = table.scan(
            Limit=limit,
        )
    logging.info(scan)
    clients = []
    with table.batch_writer() as batch:
        for each in scan['Items']:
            clients.append(each)

    logging.info(clients)

    return clients
