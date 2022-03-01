from flask import Flask
from flask_pymongo import PyMongo
import bcrypt

app = Flask(__name__)
app.config['MONGO_URI'] = 'mongodb://localhost:27017/canteen'
app.config['SECRET_KEY'] = 'dQw4w9WgXcQ'
mongo = PyMongo(app)

users_list = [{'email': 'admin@admin.com', 'password': '123456', 'username': 'admin', 'auth_type': 0, 'confirmed': 1, 'balance': 10000},
              {'email': 'test1@test.com', 'password': '123456', 'username': 'test1', 'auth_type': 1, 'confirmed': 1, 'balance': 10000},
              {'email': 'test2@test.com', 'password': '123456', 'username': 'test2', 'auth_type': 1, 'confirmed': 1, 'balance': 10000},
              {'email': 'test3@test.com', 'password': '123456', 'username': 'test3', 'auth_type': 2, 'confirmed': 1, 'balance': 10000},
              {'email': 'test4@test.com', 'password': '123456', 'username': 'test4', 'auth_type': 2, 'confirmed': 1, 'balance': 10000}]
for user in users_list:
    user['password'] = bcrypt.hashpw(user.get('password').encode('utf-8'), bcrypt.gensalt())

mongo.db.users.insert_many(users_list)
