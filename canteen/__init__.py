from flask import Flask
# from flask_pymongo import PyMongo
from pymongo import MongoClient
from flask_login import LoginManager
from flask_mail import Mail

app = Flask(__name__)
app.config['MONGO_URI'] = 'mongodb://localhost:27017/canteen'
app.config['SECRET_KEY'] = 'dQw4w9WgXcQ'
app.config['FLASK_ADMIN_SWATCH'] = 'cerulean'

# mongo = PyMongo(app)
client = MongoClient("mongodb+srv://csci3100:food-ordering@food-ordering.nonow.mongodb.net/myFirstDatabase?retryWrites=true&w=majority")
db = client.test
login_manager = LoginManager(app)

app.config['MAIL_SERVER'] = 'smtp-relay.sendinblue.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = 'csci3100canteen@gmail.com'
app.config['MAIL_PASSWORD'] = 'qM6gbtPYha8yHNd4'
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_DEFAULT_SENDER'] = 'csci3100canteen@gmail.com'
mail = Mail(app)

from canteen.user import *
from canteen.admin import *
from canteen.canteen import *
