from venv import create
from flask import Flask
from flask_pymongo import PyMongo
from flask_login import LoginManager
from flask_mail import Mail

app = Flask(__name__)
app.config['MONGO_URI'] = 'mongodb://localhost:27017/canteen'
app.config['SECRET_KEY'] = 'dQw4w9WgXcQ'
app.config['FLASK_ADMIN_SWATCH'] = 'cerulean'

mongo = PyMongo(app)
login_manager = LoginManager(app)

app.config['MAIL_SERVER'] = 'smtp.sendgrid.net'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'apikey'
app.config['MAIL_PASSWORD'] = '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'
app.config['MAIL_DEFAULT_SENDER'] = 'yiuchunto@gmail.com'
mail = Mail(app)

from canteen.routes import *

'''
ADMIN PAGE, will move to seperate .py file later
'''

from flask_admin import Admin
from flask_admin.contrib.pymongo import ModelView
from flask_wtf import Form
from wtforms import TextAreaField
import json

from canteen.models import *
from canteen.form import *

admin = Admin(app, name='microblog', template_mode='bootstrap3') #customize from theme in https://bootswatch.com/3/

class CreateUser(Form):
    user_json = TextAreaField("user_json")

class UserView(ModelView):
    column_list = ('username', 'email', 'password', 'auth_type' ,'balance')
    form = CreateUser(Form)
    user_json = json.loads( str(form.user_json.data) )
    username = user_json["username"]
    
class CanteenView(ModelView):
    column_list = ('name','longtitude','latitude','open_at','close_at','capacity','menu')
    form = CreateCanteen

class OrderView(ModelView):
    column_list = ('created_time', 'created_by_user', 'created_at_canteen','food','total_price','order_status')
    form = None

class CommentView(ModelView):
    column_list = ('posted_time','posted_by_user','posted_on_canteen','rating','paragraph')
    form = None

class DishesView(ModelView):
    column_list = ('name','in_canteen','price','ingredients','rating','image_file_name')
    form = None


admin.add_view(UserView(mongo.db['users']))
admin.add_view(CanteenView(mongo.db['canteens']))
# admin.add_view(CanteenView(mongo.db['orders']))
# admin.add_view(OrderView(mongo.db['comments']))
# admin.add_view(CanteenView(mongo.db['dishes']))

