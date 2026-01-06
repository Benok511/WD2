from flask import Blueprint, jsonify, request, g
from database import get_db
from functools import wraps
from datetime import datetime
from flask_restful import Api,Resource,reqparse
import secrets

api = Blueprint('api',__name__,url_prefix='/api')

myapi = Api(api)

def generate_api_key():
    '''
    just for ease of creating keys
    '''
    return secrets.token_hex(64) 

def apiKeyRequired(view):
    @wraps(view)
    def wrappedView(*args,**kwargs):
        api_key = request.headers.get("x-api-key")

        if not api_key:
            return {"message": "API key required"}, 401

        db = get_db()
        client = db.execute(
            "SELECT * FROM api_clients WHERE api_key = ? AND active = 1",
            (api_key,)
        ).fetchone()

        if not client:
            return {"message": "Invalid or inactive API key"}, 403

        return view(*args, **kwargs)

    return wrappedView


class Menu(Resource):
    def get(self):
        db = get_db()
        menu = db.execute('SELECT * FROM menu').fetchall()
        menu = [dict(item) for item in menu]
        return menu,200

myapi.add_resource(Menu, '/menu')

class Users(Resource):
    method_decorators = [apiKeyRequired]

    def get(self):
        db = get_db()
        users = db.execute('select user_id from customers').fetchall()
        users = [dict(user) for user in users]
        return users,200
    

myapi.add_resource(Users,'/users')

class Reviews(Resource):
    def get(self):
        db = get_db()
        reviews = db.execute('Select * from reviews')
        reviewArr = []
        for review in reviews:
            review = dict(review)
            review["date_sent"] = review["date_sent"].isoformat()
            reviewArr.append(review)
        return reviewArr,200

myapi.add_resource(Reviews,"/reviews")


class Orders(Resource):
    method_decorators = [apiKeyRequired]

    def get(self):
        db = get_db()
        orders = db.execute("Select * from placed_order")
        orders = [dict(order) for order in orders]
        return orders,200
    
myapi.add_resource(Orders,"/orders")
