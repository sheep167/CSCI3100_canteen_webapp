from flask import Flask
from flask_pymongo import PyMongo
from bson import ObjectId
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

users_list = [
    {'email': 'test1@test.com', 'password': '123456', 'username': 'test1', 'auth_type': 1, 'confirmed': 1, 'balance': 10000},
    {'email': 'test2@test.com', 'password': '123456', 'username': 'test2', 'auth_type': 1, 'confirmed': 1, 'balance': 10000},
    {'email': 'test3@test.com', 'password': '123456', 'username': 'test3', 'auth_type': 2, 'confirmed': 1, 'balance': 10000},
    {'email': 'test4@test.com', 'password': '123456', 'username': 'test4', 'auth_type': 2, 'confirmed': 1, 'balance': 10000},
    {'email': 'test@uc.com', 'password': '123456', 'username': 'uc', 'auth_type': 2, 'confirmed': 1, 'balance': 10000, 'staff_of':"UC Canteen"},
    {'email': 'test@na.com', 'password': '123456', 'username': 'na', 'auth_type': 2, 'confirmed': 1, 'balance': 10000, 'staff_of':"NA Canteen"},
    {'email': 'test@wys.com', 'password': '123456', 'username': 'wys', 'auth_type': 2, 'confirmed': 1, 'balance': 10000, 'staff_of':"WYS Canteen"},
    {'email': 'test@shho.com', 'password': '123456', 'username': 'shho', 'auth_type': 2, 'confirmed': 1, 'balance': 10000, 'staff_of':"SHHO Canteen"},
    {'email': 'test@lws.com', 'password': '123456', 'username': 'lws', 'auth_type': 2, 'confirmed': 1, 'balance': 10000, 'staff_of':"LWS Canteen"},
]
for user in users_list:
    user['password'] = bcrypt.hashpw(user.get('password').encode('utf-8'), bcrypt.gensalt())
    user['cart'] = {}
    user['image_path'] = None
    if 'staff_of' in user:
        results = mongo.db.canteens.aggregate([
                    {'$match': {"name": user['staff_of']}},
                ])
        user['staff_of'] = list(results)[0]['_id']

mongo.db.users.insert_many(users_list)


#testing only
orders_list = [
    {'at_time': '15.00', 'by_user': 'test1', 'at_canteen': 'UC Canteen', 'dishes': None, 'total_price': '100', 'waiting': 'red'},
    {'at_time': '15.01', 'by_user': 'test1', 'at_canteen': 'UC Canteen', 'dishes': None, 'total_price': '200', 'waiting': 'red'},
    {'at_time': '15.10', 'by_user': 'test1', 'at_canteen': 'UC Canteen', 'dishes': None, 'total_price': '500', 'waiting': 'yellow'},
    {'at_time': '15.20', 'by_user': 'test2', 'at_canteen': 'UC Canteen', 'dishes': None, 'total_price': '750', 'waiting': 'yellow'},
    {'at_time': '15.30', 'by_user': 'test2', 'at_canteen': 'WYS Canteen', 'dishes': None, 'total_price': '390', 'waiting': 'yellow'},
]

for order in orders_list:
    result = mongo.db.canteens.aggregate([
                {'$match': {"name": order['at_canteen']}},
            ])
    order['at_canteen'] = list(result)[0]['_id']

mongo.db.orders.insert_many(orders_list)

types_list=[
    {'name':'type a', 'at_canteen':'UC Canteen', 'dishes':None},
    {'name':'type b', 'at_canteen':'SHHO Canteen', 'dishes':None}
]

mongo.db.types.insert_many(types_list)

sets_list=[
    {}
]
mongo.db.sets.insert_many(sets_list)