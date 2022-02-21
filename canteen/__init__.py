from flask import Flask
from flask_pymongo import PyMongo
from flask_login import LoginManager

app = Flask(__name__)
app.config['MONGO_URI'] = 'mongodb://localhost:27017/canteen'
app.config['SECRET_KEY'] = 'dQw4w9WgXcQ'
mongo = PyMongo(app)
login_manager = LoginManager(app)

from canteen.routes import *
