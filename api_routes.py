from flask import Blueprint, jsonify, request, g
from database import get_db
from functools import wraps
from datetime import datetime
from flask_restful import Api,Resource,reqparse

api = Blueprint('api',__name__,url_prefix='/api')

myapi = Api(api)

class Menu(Resource):
    def get(self):
        db = get_db()
        menu = db.execute('SELECT * FROM menu').fetchall()
        menu = [dict(item) for item in menu]
        return menu,200

myapi.add_resource(Menu, '/menu')

class Users(Resource):
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
    def get(self):
        db = get_db()
        orders = db.execute("Select * from placed_order")
        orders = [dict(order) for order in orders]
        return orders,200
    
myapi.add_resource(Orders,"/orders")
