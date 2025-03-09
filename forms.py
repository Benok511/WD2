from flask_wtf import FlaskForm
from wtforms import *
from wtforms.validators import InputRequired, NumberRange, EqualTo,Length, Optional
import os


class registerForm(FlaskForm):
    user_id = StringField("Username:", validators=[InputRequired('This field is required!')])

    password = PasswordField('Password:', validators=[InputRequired('This field is required')])

    password2 = PasswordField('Confirm Password:', validators=[InputRequired('This field is required'), EqualTo('password')])

    submit = SubmitField('Register')



class SendReviewsForm(FlaskForm):
    rating = IntegerField('How would you rate our baked goods out of 10?:', validators=[InputRequired('This field is Required'),NumberRange(0,10)])

    text = TextAreaField('Enter review:', validators=[Length(5,50,'Use 5-50 characters'), InputRequired('This field is required')])

    submit = SubmitField('Submit Review!')

class addToCartForm(FlaskForm):
    item = SelectField("Select item:", choices=[], validators=[InputRequired()] )

    qty = IntegerField('Quantity', validators=[InputRequired(), NumberRange(1)])

    submit = SubmitField('Add to Cart')


class FilterMenuForm(FlaskForm):

    item_name = StringField('Item Name:')

    min_price = IntegerField('Min Price:', validators=[Optional()])

    max_price = IntegerField('Max Price:', validators=[Optional()])

    submit = SubmitField('Filter')

class LoginForm(FlaskForm):
    user_id = StringField("Username:", validators=[InputRequired('This field is required!')])

    password = PasswordField('Password:', validators=[InputRequired('This field is required')])

    submit = SubmitField()

class OrderForm(FlaskForm):

    address = StringField('Enter your address:', validators=[InputRequired()])

    instructions = TextAreaField("Special Instructions:")

    submit = SubmitField()

class ChangeUserForm(FlaskForm):

    new_userid = StringField('New Username:')

    submit = SubmitField()

class ChangePasswordForm(FlaskForm):

    current_password = PasswordField('Current password')

    new_password1 = PasswordField('New password')


    submit = SubmitField()


class UpdateMenuForm(FlaskForm):
    item_name = StringField('Item name:', validators=[InputRequired()])

    price = IntegerField('Price:', validators=[InputRequired()])

    stock = IntegerField('Stock:', validators=[InputRequired()])

    description = TextAreaField('Item Description:', validators=[InputRequired()])

    image = FileField('Image:', validators=[InputRequired()])

    submit = SubmitField()

class ViewRevenueForm(FlaskForm):

    month = SelectField('Month:', choices= ["January", "February", "March", "April", "May", "June", 
    "July", "August", "September", "October", "November", "December"])

    year = IntegerField("Year:", validators=[InputRequired()])

    submit = SubmitField()


class CreateTicketForm(FlaskForm):

    subject = StringField('Subject')

    message = TextAreaField('Enter Message:', validators=[InputRequired()])

    submit = SubmitField()

class ReplyToTicketForm(FlaskForm):

    reply = TextAreaField('Reply To Ticket:', validators=[InputRequired()])

    submit = SubmitField()


class DelFromMenu(FlaskForm):
    item = SelectField('Select Item:', choices=[])

    submit = SubmitField('Delete')

class AddStaffMemberForm(FlaskForm):
    user_id = StringField('New Staff Members Username:')

    submit = SubmitField()