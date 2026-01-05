from flask import Blueprint, jsonify, request, g
from database import get_db
from functools import wraps
from datetime import datetime
from flask_restful import Api,Resource

api = Blueprint('api',__name__,url_prefix='/api')

myapi = Api(api)

class Menu(Resource):
    def get(self):
        db = get_db()
        menu = db.execute('SELECT * FROM menu').fetchall()
        menu = [dict(item) for item in menu]
        return menu  

myapi.add_resource(Menu, '/menu')

class Users(Resource):
    def get(self):
        db = get_db()
        users = db.execute('select * from customers').fetchall()
        users = [dict(user) for user in users]
        return users
    

myapi.add_resource(Users,'/users')
