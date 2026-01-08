from flask import Blueprint, request, g
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
    '''
    Refactored admin required to do the same for api keys
    rather than requireing admin
    '''
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
    def get(self,itemid=None):
        '''
        returns full menu if no id specified in url or returns single item
        in json format
        '''
        db = get_db()
        if itemid is None:
            menu = db.execute('SELECT * FROM menu ORDER BY item_id').fetchall()
            menu = [dict(item) for item in menu]
            return menu,200
        
        else:
            item = db.execute("SELECT * FROM menu WHERE item_id = ?",(itemid,)).fetchone()
            if item is None:
                return {'message':'Item not found'},404
            return dict(item),200
        

myapi.add_resource(Menu, '/menu','/menu/<int:itemid>')

class Users(Resource):
    method_decorators = [apiKeyRequired]

    def get(self):
        '''
        returns list of users registered - only uid
        '''
        db = get_db()
        users = db.execute('select user_id from customers').fetchall()
        users = [dict(user) for user in users]
        return users,200
    

myapi.add_resource(Users,'/users')

class Reviews(Resource):
    method_decorators = [apiKeyRequired]

    def get(self):
        '''
        returns all reviews in json format
        '''
        db = get_db()
        reviews = db.execute('Select * from reviews')
        reviewArr = []
        for review in reviews:
            review = dict(review)
            review["date_sent"] = review["date_sent"].isoformat()
            reviewArr.append(review)
        return reviewArr,200

    def post(self):
        '''
        post method to add reviews via our api
        expects data sent in json with
        '''
        data = request.get_json()
        rating = data.get('rating',None)
        description = data.get('description',None)
        if not rating or not description:
            return {'message':'rating and description are required'},500 
        
        date_sent = datetime.now().date().isoformat()
        apikey = request.headers.get('x-api-key')
        db = get_db()
        user = db.execute('SELECT name from api_clients WHERE api_key = ?',(apikey,)).fetchone()
        if user:
            username=user['name']
        else:
            return {'message: api key is invalid'},403
        
        db.execute("""INSERT INTO reviews (user_id,date_sent,rating,details)
                   VALUES (?,?,?,?)""",(f'{username} user',date_sent,rating,description))
        
        db.commit()
        return {'message':'Review successfully sent'},201
        

myapi.add_resource(Reviews,"/reviews")


class Orders(Resource):
    method_decorators = [apiKeyRequired]

    def get(self):
        '''
        returns all orders - in industry this wouldnt be a function for privacy reasons
        i just made it to practice
        '''
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
