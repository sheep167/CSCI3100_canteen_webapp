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
    {'name': 'United College Student Canteen', 'latitude': '22.4210912', 'longitude': '114.2056994', 'open_at': '11:00', 'close_at': '20:45', 'capacity': 150, 'menu': [], 'image_path': "/static/images/UC/UC.jpeg", 'active_set':None},
    {'name': 'NA Canteen', 'latitude': '22.4209998', 'longitude': '114.2086538', 'open_at': '10:00', 'close_at': '20:00', 'capacity': 100, 'menu': [], 'image_path': "/static/images/NA/NA.jpg", 'active_set':None},
    {'name': 'WYS Canteen', 'latitude': '22.4221426', 'longitude': '114.2027283', 'open_at': '10:00', 'close_at': '20:00', 'capacity': 80, 'menu': [], 'image_path': "/static/images/WYS/WYS.jpg", 'active_set':None},
    {'name': 'SHHO Canteen', 'latitude': '22.4184238', 'longitude': '114.2097329', 'open_at': '10:00', 'close_at': '20:00', 'capacity': 88, 'menu': [], 'image_path': "/static/images/SHHO/SHHO.jpg", 'active_set':None},
    {'name': 'LWS Canteen', 'latitude': '22.4224862', 'longitude': '114.2043131', 'open_at': '9:00', 'close_at': '17:00', 'capacity': 85, 'menu': [], 'image_path': "/static/images/LWS/LWS.jpeg", 'active_set':None},
    {'name': 'Benjamin Franklin Centre Coffee Corner', 'latitude': '22.41897632210143', 'longitude': '114.20552342698697', 'open_at': '10:00', 'close_at': '18:00', 'capacity': 200, 'menu': [], 'image_path': "/static/images/BFC/BFC.jpeg", 'active_set':None},
    {'name': 'Chung Chi College Staff Club', 'latitude': '22.416174502784415', 'longitude': '114.20768162415987', 'open_at': '11:00', 'close_at': '15:25', 'capacity': 70, 'menu': [], 'image_path': "/static/images/CCSC/CCSC.jpeg", 'active_set':None},
    {'name': 'Orchid Lodge', 'latitude': '22.415698430860907', 'longitude': '114.20771381066638', 'open_at': '8:00', 'close_at': '18:00', 'capacity': 40, 'menu': [], 'image_path': "/static/images/OL/OL.jpeg", 'active_set':None}
]
mongo.db.canteens.insert_many(canteens_list)

users_list = [
    {'email': 'test1@test.com', 'password': '123456', 'username': 'test1', 'auth_type': 2, 'confirmed': 1, 'balance': 10000},
    {'email': 'test2@test.com', 'password': '123456', 'username': 'test2', 'auth_type': 2, 'confirmed': 1, 'balance': 10000},
    {'email': 'test3@test.com', 'password': '123456', 'username': 'test3', 'auth_type': 2, 'confirmed': 1, 'balance': 10000},
    {'email': 'test4@test.com', 'password': '123456', 'username': 'test4', 'auth_type': 2, 'confirmed': 1, 'balance': 10000},
    {'email': 'test@uc.com', 'password': '123456', 'username': 'uc', 'auth_type': 1, 'confirmed': 1, 'balance': 10000, 'staff_of':"United College Student Canteen"},
    {'email': 'test@na.com', 'password': '123456', 'username': 'na', 'auth_type': 1, 'confirmed': 1, 'balance': 10000, 'staff_of':"NA Canteen"},
    {'email': 'test@wys.com', 'password': '123456', 'username': 'wys', 'auth_type': 1, 'confirmed': 1, 'balance': 10000, 'staff_of':"WYS Canteen"},
    {'email': 'test@shho.com', 'password': '123456', 'username': 'shho', 'auth_type': 1, 'confirmed': 1, 'balance': 10000, 'staff_of':"SHHO Canteen"},
    {'email': 'test@lws.com', 'password': '123456', 'username': 'lws', 'auth_type': 1, 'confirmed': 1, 'balance': 10000, 'staff_of':"LWS Canteen"},
    {'email': 'test@bfc.com', 'password': '123456', 'username': 'bfc', 'auth_type': 1, 'confirmed': 1, 'balance': 10000, 'staff_of':"Benjamin Franklin Centre Coffee Corner"},
    {'email': 'test@ccsc.com', 'password': '123456', 'username': 'ccsc', 'auth_type': 1, 'confirmed': 1, 'balance': 10000, 'staff_of':"Chung Chi College Staff Club"},
    {'email': 'test@ol.com', 'password': '123456', 'username': 'ol', 'auth_type': 1, 'confirmed': 1, 'balance': 10000, 'staff_of':"Orchid Lodge"},
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

# add default set
for canteen in canteens_list:
    canteen_id=list(mongo.db.canteens.aggregate([
        {'$match':{'name': canteen['name']}}
    ]))[0]['_id']
    to_insert={
        'name': 'default',
        'at_canteen': ObjectId(canteen_id),
        'types': {},
    }
    mongo.db.sets.insert_one(to_insert)
    mongo.db.canteens.update_one({'_id': ObjectId(canteen_id)}, {'$set': {'active_set': to_insert['_id']} })

