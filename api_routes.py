from flask import Blueprint, jsonify, request, g
from database import get_db
from functools import wraps
from datetime import datetime

api = Blueprint('api',__name__,url_prefix='/api')


@api.route('/menu',methods = ['GET'])
def menu():
    db = get_db()
    menu = db.execute('Select * from menu')
    menu = [dict(item) for item in menu ]

    return jsonify(menu)