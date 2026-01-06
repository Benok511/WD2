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
        
        g.apiUser = client[0]
        return view(*args, **kwargs)

    return wrappedView


class Menu(Resource):
    method_decorators = [apiKeyRequired]
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
    
    def post(self):
        """
        Expects data to be sent in json format 
        with address and cart being mandatory
        and instructions optional
        cart must be in json format with k,v pair of
        itemId : [item name, item qty, total ammount for that item]
        """
        data = request.get_json()
        address = data.get('address',None)
        instructions = data.get('instructions','')
        order_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cart = data.get('cart',None)
        user = g.apiUser

        if not cart or not address:
            return {"message": "Address and cart are required"}, 400

        db = get_db()
        total = 0
        try:
            for item_id, (name, quantity) in cart.items():
                item = db.execute('SELECT price, stock FROM menu WHERE item_id = ?', (item_id,)).fetchone()
                if not item:
                    return {"message": f"Item {item_id} not found"}, 400
                if quantity > item['stock']:
                    return {"message": f"Not enough stock for {name}"}, 400
                total += item['price'] * quantity

            
            cursor = db.execute('''INSERT INTO placed_order (user_id, order_datetime, order_address, instructions, price)
                    VALUES (?,?,?,?,?)''', (user, order_datetime, address, instructions, total))
            
            order_num = cursor.lastrowid
            for id in cart:
                db.execute('''INSERT INTO in_order (order_num, item_id, quantity)
                        VALUES (?,?,?)''', (order_num, id, cart[id][1]))
                
                db.execute('''UPDATE menu
                            SET stock = stock - ?
                            WHERE item_id = ?''',(cart[id][1], id) )
            
            db.commit()
            return {'message':'Order placed successfully','order_num':order_num},201
        
        except Exception as e:
            db.rollback()
            return {'message':f'An error has occurred {str(e)}'},500
        
myapi.add_resource(Orders,"/orders")
