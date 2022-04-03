from flask import Flask
from flask_pymongo import PyMongo
import bcrypt

print('This script will DROP the CANTEEN DATABASE and recreate it.')
option = input('Y to continue / N to exit \n')
if option.lower() != 'y':
    exit()

app = Flask(__name__)
app.config['MONGO_URI'] = 'mongodb://localhost:27017/canteen'
app.config['SECRET_KEY'] = 'dQw4w9WgXcQ'
mongo = PyMongo(app)
for collection in mongo.db.list_collection_names():
    mongo.db[collection].drop()

admin = {'email': 'admin@admin.com', 'password': '123456', 'username': 'admin', 'auth_type': 0, 'confirmed': 1, 'balance': 10000}
admin['password'] = bcrypt.hashpw(admin.get('password').encode('utf-8'), bcrypt.gensalt())
mongo.db.users.insert_one(admin)

users_list = [
    {'email': 'test1@test.com', 'password': '123456', 'username': 'test1', 'auth_type': 1, 'confirmed': 1, 'balance': 10000},
    {'email': 'test2@test.com', 'password': '123456', 'username': 'test2', 'auth_type': 1, 'confirmed': 1, 'balance': 10000},
    {'email': 'test3@test.com', 'password': '123456', 'username': 'test3', 'auth_type': 2, 'confirmed': 1, 'balance': 10000},
    {'email': 'test4@test.com', 'password': '123456', 'username': 'test4', 'auth_type': 2, 'confirmed': 1, 'balance': 10000}
]
for user in users_list:
    user['password'] = bcrypt.hashpw(user.get('password').encode('utf-8'), bcrypt.gensalt())
    user['cart'] = {}
    user['image_path'] = None
print(users_list)
mongo.db.users.insert_many(users_list)

# must be updated
canteens_list = [
    {'name': 'UC Canteen', 'latitude': '22.4210912', 'longitude': '114.2056994', 'open_at': '10:00', 'close_at': '20:00', 'capacity': 150, 'menu': []},
    {'name': 'NA Canteen', 'latitude': '22.4209998', 'longitude': '114.2086538', 'open_at': '10:00', 'close_at': '20:00', 'capacity': 100, 'menu': []},
    {'name': 'WYS Canteen', 'latitude': '22.4221426', 'longitude': '114.2027283', 'open_at': '10:00', 'close_at': '20:00', 'capacity': 80, 'menu': []},
    {'name': 'SHHO Canteen', 'latitude': '22.4184238', 'longitude': '114.2097329', 'open_at': '10:00', 'close_at': '20:00', 'capacity': 88, 'menu': []},
    #I (Maneemala) added LWS Canteen through a web page
    {'name': 'LWS Canteen', 'latitude': '22.4224862', 'longitude': '114.2043131', 'open_at': '9:00', 'close_at': '17:00', 'capacity': 85, 'menu': []}
]

mongo.db.canteens.insert_many(canteens_list)
