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

from canteen.user import *
from canteen.admin import *
from canteen.canteen import *
