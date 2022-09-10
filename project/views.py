from flask import jsonify, request
from flask_restful import Resource
from .database import get_carer, get_paginated_carers, get_policy, get_paginated_policies

# The Homepage


def home():
    return '<h1>Insurance Service</h1><p>Created By Kenan</p>'

#TODO add policies
# Handles /carers route
class ClientList(Resource):
    def get(self):
        return jsonify(get_paginated_carers(
            last=request.args.get('last', None),
            limit=request.args.get('limit', 25)
        ))

# Handles /carers/<int:carer_id> route


class Client(Resource):
    def get(self, carer_id):
        return jsonify(get_carer(
            id=carer_id
        ))

# Handles /policies route
class PolicyList(Resource):
    def get(self):
        return jsonify(get_paginated_policies(
            last=request.args.get('last', None),
            limit=request.args.get('limit', 25)
        ))

# Handles /policies/<int:carer_id>/<int:policy_start_date> route


class Policy(Resource):
    def get(self, carer_id, policy_start_date):
        return jsonify(get_policy(
            id=carer_id,
            policy_start=policy_start_date
        ))
