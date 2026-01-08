from flask import *
from datetime import datetime
from forms import *
from database import get_db,close_db
from werkzeug.security import generate_password_hash,check_password_hash
from werkzeug.utils import secure_filename
from flask_session import Session
from functools import wraps
import os
from api_routes import api,generate_api_key

'''
The file upload code was learned and adapted from https://flask.palletsprojects.com/en/stable/patterns/fileuploads/

2 types of Users, Admins and customers, to login as an admin the Username is "admin" and the password is also "admin".
To login as a customer just register as usual.

Passing data through url_for in the jinja was adapted from https://stackoverflow.com/questions/7478366/create-dynamic-urls-in-flask-with-url-for

for the support section the user can create tickets then the admin can respond and when the user checks the ticket the admin
response will be there
'''

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static')
ALLOWED_EXTENSIONS = ['png','jpg','jpeg']

app = Flask(__name__)
app.config["SECRET_KEY"] = "this-is-my-secret-key"
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = 'filesystem'

#adding api connection
app.register_blueprint(api,url_prefix='/api')


#file upload setup
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1000 * 1000 #max filesize of 16MB

Session(app)
app.teardown_appcontext(close_db)

@app.before_request
def load_logged_in_user():
    g.user = session.get('user_id',None)
    g.is_admin = session.get('is_admin',None)


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if g.user is None:
            return redirect(url_for('login', next = request.url))
        return view(*args, **kwargs)
    return wrapped_view

def admin_required(view): #just took your code for the login decorator and changed it to do the same for admin-only pages   
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if g.is_admin is None:
            return redirect(url_for('restricted'))
        return view(*args, **kwargs)
    return wrapped_view

@app.route('/restricted')
def restricted():
    return render_template('error.html', title = 'RESTRICTED', message = 'You are not permitted to see this page')



@app.route('/')
def index():
    db = get_db()

    reviews = db.execute('''SELECT * FROM reviews''').fetchmany(5)

    return render_template('index.html', title = 'Welcome!', reviews = reviews)


@app.route('/register', methods=["GET", 'POST'])
def register():
    form = registerForm()
    if form.validate_on_submit():
        user_id = form.user_id.data
        password = form.password.data 
        db = get_db()
        clash = db.execute('''Select * from customers Where user_id = ?''', (user_id,)).fetchone()

        if clash is not None:
            form.user_id.errors.append('This username is taken')
        else:
            db.execute(''' INSERT INTO customers (user_id, password) 
                           VALUES (?, ?);''', (user_id, generate_password_hash(password)))

            db.commit()

            return redirect(url_for('login'))
    
    return render_template('register.html', form=form, title = "Registration")

    
@app.route('/login', methods=['GET','POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user_id = form.user_id.data
        password = form.password.data
        db = get_db()
        in_db = db.execute('''SELECT * FROM customers WHERE user_id = ?''', (user_id,)).fetchone()

        if in_db is None:
            form.user_id.errors.append('This user does not exist!')

        elif not check_password_hash(in_db['password'], password):
            form.password.errors.append('Incorrect Password')
            
        else:
            session.clear()
            session['user_id'] = user_id
            if in_db['is_admin'] == 1:
                session['is_admin'] = True
            session.modified = True
            next_page = request.args.get('next')
            if not next_page:
                next_page = url_for('index')
            return redirect(next_page)
        
    return render_template('login.html', form=form, title = 'Login')
    

@app.route('/logout')
def logout():
    session.clear()
    session.modified = True
    return redirect(url_for('index'))


@app.route('/menu', methods = ["GET", 'POST'])
def menu():
    form = FilterMenuForm()
    db = get_db()
    if form.validate_on_submit():
        item_name = form.item_name.data
        min_price = form.min_price.data
        max_price = form.max_price.data

        
        if item_name != '' and min_price is None and max_price is None:
            menu = db.execute("""SELECT * FROM menu WHERE item_name LIKE '%' || ? || '%' """, (item_name,)).fetchall()
        
        elif item_name == '' and min_price is not None and max_price is None:
            menu = db.execute("""SELECT * FROM menu WHERE price >= ?""", (min_price,)).fetchall()
        
        elif item_name == '' and min_price is None and max_price is not None:
            menu = db.execute("""SELECT * FROM menu WHERE price <= ?""", (max_price,)).fetchall()
        
        elif item_name != '' and min_price is not None and max_price is None:
            menu = db.execute("""SELECT * FROM menu WHERE price >= ? AND item_name LIKE '%' || ? || '%' """, (min_price,item_name)).fetchall()
        
        elif item_name != '' and min_price is None and max_price is not None:
            menu = db.execute("""SELECT * FROM menu WHERE price <= ? AND item_name LIKE '%' || ? || '%' """, (max_price,item_name)).fetchall()

        elif item_name == '' and min_price is not  None and max_price is not None:
            menu = db.execute("""SELECT * FROM menu WHERE price BETWEEN ? AND ? """, (min_price,max_price)).fetchall()
        
        elif item_name != '' and min_price is not None and max_price is not None:
            menu = db.execute("""SELECT * FROM menu WHERE price BETWEEN ? AND ? AND item_name LIKE '%' || ? || '%' """, (min_price, max_price ,item_name)).fetchall()
        
        else:
            menu = db.execute("""SELECT * FROM menu""").fetchall()



    else:
        menu = db.execute("""SELECT * FROM menu""").fetchall()

    return render_template('menu.html', menu=menu, title = "Menu", form = form)

@app.route('/add-to-cart', methods = ['GET', 'POST'])
@login_required
def add_to_cart():
    message = ''
    form = addToCartForm()
    db = get_db()
    choices = db.execute(''' SELECT * FROM menu''').fetchall()
    
    for choice in choices:
        form.item.choices.append(choice['item_name'])

    if form.validate_on_submit():
        item = form.item.data
        qty = form.qty.data

        check_stock = db.execute('''SELECT * from menu WHERE item_name = ?''', (item,)).fetchone()

        stock = check_stock['stock']
        id = check_stock['item_id']
        if qty > stock:
            message = f"Sorry we do not have enough stock to fulfil this order. We have {check_stock['stock']} {item}'s in stock"

        else:
            if 'cart' not in session:
                session['cart'] = {}
            if item not in session['cart']:
                session['cart'][id] = [item , qty , check_stock['price'] * qty, check_stock['image']]
            else:
                session['cart'][id][1] += qty
                session['cart'][id][2] = check_stock['price']  * session['cart'][id][1]
            
            
            session.modified = True
            message = 'Item has been successfully added to your cart!'
    return render_template('add_to_cart.html', form = form, message = message, title = 'Add to Cart')


@app.route('/remove_from_cart/<id>')
@login_required
def remove(id):
    id = int(id)

    session['cart-total'] -= session['cart'][id][2]

    del session['cart'][id]
    session.modified = True

    return redirect(url_for('cart'))

@app.route('/increment_cart_item/<id>')
@login_required
def increment(id):
    id = int(id)
    message = ''

    db = get_db()
    check = db.execute(''' SELECT * FROM menu WHERE item_id = ? ''', (id,)).fetchone()

    if check['stock'] < session['cart'][id][1] + 1:
        message = 'Sorry we do not have enough to fulfil your order'
    
    else:
        session['cart'][id][1] += 1
        session['cart'][id][2] = check['price']  * session['cart'][id][1]
        message = 'Item added Successfully'
        session.modified = True

    return redirect(url_for('cart', message = message))

@app.route('/decrement_cart_item/<id>')
@login_required
def decrement(id):
    id = int(id)
    

    db = get_db()
    check = db.execute(''' SELECT * FROM menu WHERE item_id = ? ''', (id,)).fetchone()

    if session['cart'][id][1] - 1 == 0:
        del session['cart'][id]
    else:
        session['cart'][id][1] -= 1
        session['cart'][id][2] = check['price'] * session['cart'][id][1]
        
    session.modified = True
    return redirect(url_for('cart'))


@app.route('/order', methods = ['GET', 'POST'])
@login_required
def order():
    form = OrderForm()
    if form.validate_on_submit():
        address = form.address.data
        instructions = form.instructions.data
        order_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        db = get_db()
        db.execute('''INSERT INTO placed_order (user_id, order_datetime, order_address, instructions, price)
                   VALUES (?,?,?,?,?)''', (g.user, order_datetime, address, instructions, session['cart-total']))
        
        db.commit()

        get_order_num = db.execute('''SELECT * FROM placed_order WHERE user_id = ? AND order_datetime = ? AND order_address = ? AND instructions = ? AND price = ?'''
                   , (g.user, order_datetime, address, instructions, session['cart-total'])).fetchone()
        
        order_num = get_order_num['order_num']

        for id in session['cart']:
            db.execute('''INSERT INTO in_order (order_num, item_id, quantity)
                       VALUES (?,?,?)''', (order_num, id, session['cart'][id][1]))
            
            db.execute('''UPDATE menu
                        SET stock = stock - ?
                        WHERE item_id = ?''',(session['cart'][id][1], id) )
        
        db.commit()

        del session['cart']
        session['cart-total'] = 0
        session.modified = True

        return render_template('order_complete.html', title = 'Order Completed')

    return render_template('complete_order.html', form = form, cart_total = session['cart-total'], title = 'Complete Order')


@app.route('/view_profile')
@login_required
def view_profile():
        db = get_db()
        order_details = db.execute('''SELECT * FROM placed_order WHERE user_id = ?''', (g.user,)).fetchall()
        total_spent = db.execute('''SELECT SUM(price) FROM placed_order WHERE user_id = ?''', (g.user,)).fetchone()

        return render_template('profile.html', order_details = order_details, total_spent = total_spent, title = 'Your Profile')


@app.route('/edit_profile', methods = ['GET', 'POST'])
@login_required
def edit_profile ():
    change_user_form = ChangeUserForm()
    change_password_form = ChangePasswordForm()
    message = ''
    
    if change_user_form.validate_on_submit():
        if change_user_form.new_userid.data is None or change_user_form.new_userid.data == '':
            pass
        else:
            db = get_db()
            print(db)
            new_userid = change_user_form.new_userid.data
            check_clash = db.execute(''' SELECT user_id FROM customers WHERE user_id = ?''', (new_userid,)).fetchone()
            if check_clash is not None:
                change_user_form.new_userid.errors.append('This username is already in use')

            else:

                db.execute('''UPDATE customers SET user_id = ? WHERE user_id = ?''', (new_userid,g.user))

                db.execute('''UPDATE placed_order SET user_id = ? WHERE user_id = ?''', (new_userid,g.user))

                db.execute('''UPDATE reviews SET user_id = ? WHERE user_id = ? ''', (new_userid,g.user))

                db.execute('''UPDATE support SET user_id = ? WHERE user_id = ? ''', (new_userid,g.user))


                db.commit()
                session['user_id'] = new_userid
                
                message = 'Username Successfully Updated'
                

    if change_password_form.validate_on_submit():
        if change_password_form.new_password1.data is None or change_password_form.new_password1.data == '':
            pass
        else:

            db = get_db()
            current_password = change_password_form.current_password.data
            new_password = change_password_form.new_password1.data

            check_password =  db.execute('''SELECT password FROM customers WHERE user_id = ? ''', (g.user,)).fetchone()

            if not check_password_hash(check_password['password'], current_password):
                change_password_form.current_password.errors.append('Incorrect Password')
            
            else:
                db.execute('''UPDATE customers SET password = ? WHERE user_id = ?''', (generate_password_hash(new_password), g.user))
                db.commit()
                message = 'Password Successfully Updated'


            
    
    return render_template('edit_profile.html', form1 = change_user_form, form2 = change_password_form, title = 'Edit Profile', message=message)






        

@app.route("/send_review", methods=["GET", "POST"])
@login_required
def send_review():
    form = SendReviewsForm()
    message = ''
    if form.validate_on_submit():
        
        rating = form.rating.data
        text = form.text.data
        date = datetime.now().date()
        db = get_db()
        db.execute('''INSERT INTO reviews (user_id,date_sent,rating, details)
                   VALUES (?,?,?,?)''',(g.user,date,rating,text))
        db.commit()
        message = 'Review submitted successfully!'
        
    return render_template('send_review.html', form = form, message = message, title = 'Leave a Review!')

@app.route('/cart')
@login_required
def cart(): 
    menu = None
    if 'cart' not in session:
        session['cart'] = {}
        session['cart-total'] = 0
        session.modified = True
    else:
        db = get_db()
        menu = db.execute('''SELECT * FROM MENU''').fetchall()
        total = 0
        for id in session['cart']:
            total += session['cart'][id][2]
        session['cart-total'] = total
    return render_template('cart.html', cart = session['cart'], total = session['cart-total'], title = 'Your Cart', menu = menu )
    
@app.route('/admin-tools')
@login_required
@admin_required
def admin_tools():
    db = get_db()

    orders = db.execute('''SELECT * FROM placed_order WHERE order_progress = "In Progress" ''').fetchall()
    


    most_popular_item_id = db.execute('''SELECT item_id, MAX(total_qty) FROM 
    (SELECT item_id, SUM(quantity) AS total_qty
    FROM in_order
    GROUP BY item_id) AS item_totals;''').fetchone()

    most_popular_item = db.execute('''SELECT * From menu WHERE item_id = ?''', (most_popular_item_id[0],)).fetchone()

    return render_template('admin.html', orders = orders, most_popular_item = most_popular_item, title = 'Current Orders')

@app.route("/update-stock", methods = ["GET","POST"])
@login_required
@admin_required
def update_stock():
    message = ''
    form = UpdateStockForm()

    db = get_db()
    choices = db.execute('''SELECT * FROM menu''').fetchall()
    for choice in choices:
        form.item.choices.append(choice['item_name'])

    if form.validate_on_submit():
        item = form.item.data
        qty = form.qty.data

        db.execute('''UPDATE menu SET stock = stock + ? WHERE item_name = ? ''', (qty,item))
        db.commit()
        message = 'Stock successfully updated'

    return render_template('update_stock.html', form=form, message=message, title='Update Stock')

@app.route('/update-menu', methods = ["GET", "POST"])
@login_required
@admin_required
def update_menu():
    return render_template('update_menu.html', title = 'Update Menu')

@app.route('/add-to-menu', methods = ["GET","POST"])
@login_required
@admin_required
def add_to_menu():
    message = ''
    form = UpdateMenuForm()

    if form.validate_on_submit():
        item_name = form.item_name.data
        price = form.price.data
        stock = form.stock.data
        image = form.image.data
        description = form.description.data

       #file upload code learned from flask documentation link provided on, os module learned in CS1117

        image_type = image.filename.split('.')
        
        if image_type[-1].lower() not in ALLOWED_EXTENSIONS:
            form.image.errors.append('Invalid File Type!')

        else:
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            db = get_db()
            db.execute('''INSERT INTO menu (item_name, price, stock, image, description)    
                        VALUES (?,?,?,?,?)''',(item_name,price,stock,filename,description))
            db.commit()

            message = 'New item added successfully!'
            
        

    return render_template('add_to_menu.html', form = form, title='Add New Menu Item', message = message)

@app.route('/delete-menu', methods = ['GET',"POST"])
@login_required
@admin_required
def delete_menu_item():
    form = DelFromMenu()
    message = ''
    db = get_db()
    items = db.execute('''SELECT * FROM MENU''').fetchall()

    for item in items:
        form.item.choices.append(item['item_name'])


    if form.validate_on_submit():
        item = form.item.data
        
        image = db.execute('''SELECT * FROM menu WHERE item_name = ? ''',(item,)).fetchone()
        os.remove(UPLOAD_FOLDER + '/' + image['image'])

        db.execute('''DELETE FROM MENU WHERE item_name = ?''',(item,))
        db.commit()

        

        message = 'Item Successfully Removed'
    
    return render_template('delete_from_menu.html', title = 'Delete From Menu', form = form, message = message)


@app.route('/mark-complete/<id>')
@login_required
@admin_required
def mark_complete(id):
    id = int(id)
    db = get_db()

    db.execute('''UPDATE placed_order SET order_progress = "Complete" WHERE order_num = ?''', (id,))
    db.commit()
    return redirect(url_for('admin_tools'))



@app.route('/order-contents/<id>')
@login_required
def order_contents(id):
    id = int(id)

    db = get_db()
    check_user = db.execute('''SELECT * FROM placed_order WHERE order_num = ?''', (id,)).fetchone()

    if check_user[1] != g.user and g.is_admin is None:
        return render_template('error.html', title = 'Restricted', message = 'This order number is not for your order!')
    
    item_names = {}
    get_item_names = db.execute('''SELECT * FROM MENU''').fetchall()

    for item in get_item_names:
        item_names[item['item_id']] = item['item_name']
        
    
    items_in_order = db.execute('''SELECT * FROM in_order WHERE order_num = ?''', (id,)).fetchall()

    return render_template('admin_order_contents.html', title = 'Order Contents', item_names = item_names, items_in_order = items_in_order, order_num = id)



@app.route('/financials', methods = ["GET", "POST"]) #only feb and march 2025 have proper outputs for obvious reasons
@login_required
@admin_required
def financials():
    form = ViewRevenueForm()
    months = {"January": "01", "February": "02", "March": "03", "April": "04", "May": "05",
    "June": "06", "July": "07", "August": "08", "September": "09", "October": "10", "November": "11",
    "December": "12"}
    month = None
    year = None
    orders = None
    revenue = None
    yearly_rev = None
    most_popular_item_monthly = None
    message = ''

    if form.validate_on_submit():
        month = form.month.data
        month = months.get(month,None)

        year = form.year.data

        db = get_db()
        orders = db.execute('''SELECT * FROM placed_order 
                            WHERE order_datetime BETWEEN ? AND ? AND order_progress = 'Complete' ''', 
                            (f"{year}-{month}-01",f"{year}-{month}-31")).fetchall()
        
        revenue = db.execute('''SELECT SUM(price) FROM placed_order 
                            WHERE order_datetime BETWEEN ? AND ? AND order_progress = 'Complete' ''', 
                            (f"{year}-{month}-01)",f"{year}-{month}-31")).fetchone()
        
        yearly_rev = db.execute('''SELECT SUM(price) FROM placed_order 
                            WHERE order_datetime BETWEEN ? AND ? AND order_progress = 'Complete' ''', 
                            (f"{year}-01-01)",f"{year}-12-31")).fetchone()
        
        most_popular_item_monthly = db.execute('''
        SELECT *
        FROM menu 
        WHERE item_id = (
            SELECT item_id 
            FROM (
                SELECT in_order.item_id, SUM(in_order.quantity) AS total_qty
                FROM in_order
                WHERE in_order.order_num IN (
                    SELECT order_num 
                    FROM placed_order 
                    WHERE order_datetime BETWEEN ? and ?
                )
                GROUP BY in_order.item_id
                ORDER BY total_qty DESC
                LIMIT 1
            ) AS item_totals
        )
    ''',(f"{year}-{month}-01)",f"{year}-{month}-31")).fetchone()
        
        if len(orders) == 0:
            message = 'No orders during this period!'

    return render_template('financials.html', form=form, title='View Revenue', month = form.month.data, year = year, message = message,
                           orders = orders, most_popular_item_monthly = most_popular_item_monthly, revenue = revenue, yearly_rev = yearly_rev)


@app.route('/support')
@login_required
def support():
    return render_template('support.html', title = 'Support')

@app.route('/create-support-ticket', methods = ['GET', 'POST'])
@login_required
def create_ticket():
    form = CreateTicketForm()
    message = ''
    if form.validate_on_submit():
        ticket_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        subject = form.subject.data
        message = form.message.data

        db = get_db()
        db.execute('''INSERT INTO support (user_id, ticket_datetime, subject, message)
                   VALUES (?,?,?,?)''',(g.user,ticket_datetime,subject,message))
        db.commit()

        message = 'Support ticket created successfuly!'

    return render_template('create_support_ticket.html', title = 'Create Ticket', form = form, message = message)


@app.route('/view-tickets')
@login_required
def view_tickets():
    db = get_db()

    tickets = db.execute('''SELECT * FROM support WHERE user_id = ?''',(g.user,)).fetchall()

    return render_template('view_tickets.html', title = 'View Tickets', tickets = tickets)

@app.route('/view-ticket-details/<ticket_id>', methods = ['GET', 'POST']) 
@login_required #you have to refresh the page after submitting a reply to a support ticket to see the reply has been sent
def view_ticket_details(ticket_id):
    ticket_id = int(ticket_id)
    form = None

    db = get_db()
    details = db.execute('''SELECT * FROM support WHERE ticket_num = ?''',(ticket_id,)).fetchone()

    if g.user != details['user_id'] and g.is_admin is None:
        return redirect(url_for('restricted'))
    
    if g.is_admin is not None:
        form = ReplyToTicketForm()
        
        if form.validate_on_submit():
            reply = form.reply.data
            reply_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            db.execute('''UPDATE support SET admin_user_id = ?, reply_datetime = ?, reply = ? 
                       WHERE ticket_num = ?''',(g.user,reply_datetime,reply,ticket_id))
            
            db.commit()
        

    return render_template('view_ticket_details.html', title = 'View Ticket Details', ticket_num = ticket_id, details = details, form = form)

@app.route('/admin-view-tickets')
@login_required
@admin_required
def admin_view_tickets():
    db = get_db()
    tickets = db.execute('''SELECT * FROM support WHERE reply = "" ''').fetchall()

    return render_template('view_tickets.html', tickets = tickets, title = 'View Unanswered Tickets')

@app.route('/add-new-staff', methods = ["GET", "POST"])
@login_required
@admin_required
def add_new_staff():
    form = AddStaffMemberForm()
    message = ''
    if form.validate_on_submit():
        user_id = form.user_id.data

        db = get_db()

        check_user = db.execute('''SELECT * FROM customers WHERE user_id = ?''', (user_id,)).fetchone()

        if check_user is None:
            form.user_id.errors.append('This user does not exist')
        
        else:
            db.execute('''UPDATE customers SET is_admin = 1 WHERE user_id = ?''', (user_id,))
            db.commit()
            message = 'Staff Member successfully added'

    return render_template('add_staff.html', form = form, message = message, title = 'Add New Staff Members')

@app.route('/view-staff', methods =["GET", 'POST'])
@login_required
@admin_required
def view_staff():
    db = get_db()
    staff =  db.execute('''SELECT * FROM customers WHERE is_admin = 1''').fetchall()

    return render_template('view_staff.html', staff = staff, title = 'Employee Roster' )

@app.route('/remove-staff/<user_id>')
@login_required
@admin_required
def remove_staff(user_id):
    if user_id != g.user: #not allowing to remove yourself ass admin
        db = get_db()
        db.execute("""UPDATE customers SET is_admin = 0 WHERE user_id = ?""", (user_id,))
        db.commit()

    return redirect(url_for('view_staff'))

@app.route('/view-reviews-admin')
@login_required
@admin_required
def view_reviews ():
    db = get_db()
    reviews = db.execute("""SELECT * FROM reviews""").fetchall()

    return render_template("view_reviews.html", title = 'View Reviews', reviews = reviews)

@app.route('/delete-review/<review_num>')
@login_required
@admin_required
def delete_review(review_num):
    review_num = int(review_num)
    db = get_db()
    db.execute("""DELETE FROM reviews WHERE review_num = ?""", (review_num,))
    db.commit()

    return redirect(url_for('view_reviews'))

@app.route('/add-api-client', methods=["GET","POST"])
@login_required
@admin_required
def addApiClient():
    form = ApiClientForm()
    message = ''
    if form.validate_on_submit():
        name = form.name.data
        apiKey = generate_api_key()
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        db = get_db()
        db.execute('''INSERT INTO api_clients(name,api_key,created_at)
                   VALUES (?,?,?)''',(name,apiKey,created_at))
        db.commit()
        message = f'client successfully added. API KEY: {apiKey}'
    
    return render_template('AddApiClient.html',form=form,message=message,title='Add Api Client')

@app.route('/credits')
def credits():
    return render_template('credits.html', title = 'Credits')

@app.errorhandler(404)
def cant_park_there_mate(error):
    return render_template('error.html', title = '404 Error', message = 'You tried to access a page that doesnt exist, perhaps you mispelled it!')




