import datetime
from collections import Counter
from bson import ObjectId
from canteen import app, mongo, mail
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user, login_required
from .form import UserRegistrationForm, UserLoginForm
from .models import Users, LoginUsers
import bcrypt
from itsdangerous import URLSafeTimedSerializer, SignatureExpired
from werkzeug.utils import secure_filename
from flask_mail import Message
from flask_wtf import FlaskForm  # 1.
from wtforms import StringField  # 2.
from wtforms.validators import DataRequired  # 3.
import threading
import time

"""
order page
- add_order: add to order_list
- finideh_order: move from order_list to finished_order_list and noti to user
- clear_order:
- clear_finished_order:

menu page:
- create_type
- add_menu
- delete_menu
- edit_menu
- create_set
- edit_set
- delete_set
"""


@app.route('/canteen_home', methods=['GET'])
def canteen_home():
    data = [
        {'dish': 'a', 'price': 1, 'sold': 1},
        {'dish': 'b', 'price': 2, 'sold': 2},
        {'dish': 'c', 'price': 3, 'sold': 3},
        {'dish': 'd', 'price': 4, 'sold': 4},
        {'dish': 'e', 'price': 5, 'sold': 5},
    ]
    dishes = 0
    revenue = 0
    for orders in data:
        dishes += orders['sold']
        revenue += orders['price'] * orders['sold']

    return render_template('canteen/canteen_home.html', data=data, dishes=dishes, revenue=revenue)

@app.route('/canteen_account', methods=['GET', 'POST'])
def canteen_account():
    return render_template('canteen/canteen_account.html')

@app.route('/canteen_account/<canteen_id>/order', methods=['GET', 'POST'])
@login_required
def order_page(canteen_id):
    if current_user.auth_type > 1:
        return 'Not Authorized', 403

    if request.method == 'GET':
        results = mongo.db.orders.aggregate([
            {'$match': {'at_canteen': ObjectId(canteen_id)}}  # edit!!!
        ])
    orders = list(results)
    

    for order in orders :
        time = datetime.datetime.strptime(order['at_time'][2:], '%y-%m-%d %H:%M:%S')
        print(datetime.datetime.now())
        duration = datetime.datetime.now() - time
        duration_in_s = duration.total_seconds()      
        print(duration_in_s)
        if duration_in_s >= 15 * 60 :
            order['order_status'] = 'rush'
        elif duration_in_s >= 5 * 60 :
            order['order_status'] = 'normal'
        mongo.db.orders.update_one({'_id': ObjectId(order['_id'])}, {'$set': {'order_status' : order['order_status']}})


    return render_template('canteen/order.html', orders=orders)

@app.route('/canteen_account/<canteen_id>/menu', methods=['GET', 'POST'])
@login_required
def menu_page(canteen_id):
    if current_user.auth_type > 1:
        return 'Not Authorized', 403

    if request.method == 'POST':
        set_name=request.form.get('active-set')

        _set=list(mongo.db.sets.aggregate([
            {'$match':{'name':set_name}}
        ]))[0]
        
        target_types=_set['types']
        print(target_types)
        at_canteen=_set['at_canteen']

        active_dishes_id=[]
        for _type in target_types:
            for dish_name in target_types[_type]:
                dish_id=list(mongo.db.dishes.aggregate([
                    {'$match':{'name':dish_name}}
                ]))[0]['_id']
                active_dishes_id.append(dish_id)

        mongo.db.canteens.update_one({'_id': ObjectId(at_canteen)}, {'$set': {'menu' : active_dishes_id}})

        


        return redirect('/canteen_account/%s/menu' % canteen_id)    

    if request.method == 'GET':
        results = mongo.db.sets.aggregate([
            {'$match': {'at_canteen': ObjectId(canteen_id)}}
        ])
        sets = list(results)
        for _set in sets:
            to_remove = []
            for _type in _set['types']:
                if len(_set['types'][_type]) == 0:
                    to_remove.append(_type)
 
            for _type in to_remove:
                del _set['types'][_type]

        results = mongo.db.types.aggregate([
            {'$match': {'at_canteen': ObjectId(canteen_id)}}
        ])
        types = list(results)
    return render_template('canteen/menu.html', canteen_id=canteen_id, sets=sets, types=types)

@app.route('/canteen_account/finish/<order_id>', methods=['GET', 'POST'])
@login_required
def finish_order(order_id):
    if request.method == 'GET':
        order = mongo.db.orders.aggregate([
            {'$match': {'_id': ObjectId(order_id)}}
        ])

        order = list(order)

        print(order_id)

        mongo.db.orders.update_one({'_id': ObjectId(order_id)}, {'$set': {'order_status' : 'finished'}})

    return redirect('/canteen_account/%s/order' % order[0]['at_canteen'])

@app.route('/canteen_account/<canteen_id>/add/set', methods=['GET', 'POST'])
@login_required
def add_set(canteen_id):
    if current_user.auth_type > 1:
        return 'Not Authorized', 403

    if request.method == 'POST':
        _set_name = request.form.get('set-name')

        if _set_name == '':
            flash('Please add your set name', category='info')
        else:
            _dish_dict = {}
            types = list(mongo.db.types.aggregate([
                {'$match': {'at_canteen': ObjectId(canteen_id)}}
            ]))
            for _type in types:
                checkboxAns = request.form.getlist(_type['name'])
                _dish_dict[_type['name']] = checkboxAns
            
            sets_num = len(list(mongo.db.sets.aggregate([])))
            print(sets_num)

            mongo.db.sets.insert_one({
                'name': _set_name,
                'at_canteen': ObjectId(canteen_id),
                'types': _dish_dict,
                'active': 0
            })
            return redirect('/canteen_account/%s/menu' % canteen_id)

    types = []
    if request.method == 'GET':
        results = mongo.db.types.aggregate([
            {'$match': {'at_canteen': ObjectId(canteen_id)}}
        ])
        types = list(results)

    return render_template('canteen/add_set.html', canteen_id=canteen_id, types=types)

@app.route('/canteen_account/<canteen_id>/add/type', methods=['GET', 'POST'])
@login_required
def add_type(canteen_id):
    if current_user.auth_type > 1:
        return 'Not Authorized', 403

    typename = ''
    if request.method == 'POST':
        typename = request.form['typename']
        if typename == '':
            flash('Please add your type name', category='info')
        if len(typename) >= 300:
            flash('300 characters limit exceeded', category='warning')
        else:
            mongo.db.types.insert_one({
                'name': typename,
                'at_canteen': ObjectId(canteen_id),
                'dishes': []
            })
        return redirect('/canteen_account/%s/menu' % canteen_id)
    return render_template('canteen/add_type.html')

@app.route('/canteen_account/<canteen_id>/edit/sets/<set_id>', methods=['GET', 'POST'])
def edit_set(canteen_id, set_id):
    if current_user.auth_type > 1:
        return 'Not Authorized', 403


    print("method")
    print(request.method)
    if request.method == 'POST':
        _set_name = request.form.get('set-name')
        print("hello")
        print(_set_name)
        if _set_name == '':
            flash('Please add your set name', category='info')
        else:
            _dish_dict = {}
            types = list(mongo.db.types.aggregate([
                {'$match': {'at_canteen': ObjectId(canteen_id)}}
            ]))
            for _type in types:
                checkboxAns = request.form.getlist(_type['name'])
                _dish_dict[_type['name']] = checkboxAns
            print(checkboxAns)
            print(_set_name)
            mongo.db.sets.update_one({'_id': ObjectId(set_id)}, {'$set': {'types': _dish_dict, 'name':_set_name} })

            return redirect('/canteen_account/%s/menu' % canteen_id)

    # types=[]
    if request.method == 'GET':
        types = list(mongo.db.types.aggregate([
            {'$match': {'at_canteen': ObjectId(canteen_id)}}
        ]))
        _set = list(mongo.db.sets.aggregate([
            {'$match': {'_id': ObjectId(set_id)}}
        ]))[0]
        # print(_set)
        type_with_indicated = []
        for _type in types:
            for_type = [_type['name']]
            for_type.append([])
            for dish in _type['dishes']:
                if _set['types']:
                    if dish['name'] in _set['types'][_type['name']]:
                        for_type[1].append([dish['name'], 1])
                    else:
                        for_type[1].append([dish['name'], 0])
                else:
                    for_type[1].append([dish['name'], 0])
            type_with_indicated.append(for_type)
        print(type_with_indicated)
    return render_template('canteen/edit_set.html', canteen_id=canteen_id, type_with_indicated=type_with_indicated,
                           _set=_set)

@app.route('/canteen_account/<canteen_id>/add/menu/<typeID>', methods=['GET', 'POST'])
def add_menu(canteen_id, typeID):
    if current_user.auth_type > 1:
        return 'Not Authorized', 403

    def isFloat(num):
        try:
            float(num)
            return True
        except:
            return False

    if request.method == 'POST':
        menuName = request.form.get('menu-name')
        price = request.form.get('price')
        if menuName == '':
            flash('Please add your menu name', category='info')
        if len(menuName) >= 300:
            flash('300 characters limit exceeded', category='warning')
        if price == '':
            flash('Please input your menu price', category='info')
        if not isFloat(price):
            flash('Please input your price as a number', category='warning')
        else:

            # update dishes
            mongo.db.dishes.insert_one({
                'name': str(menuName),
                'at_canteen': ObjectId(canteen_id),
                'price': float(price),
                'in_type': ObjectId(typeID),
                'ingredients':[]
            })

            dish_id = list(mongo.db.dishes.aggregate([
                {'$match': {'name':str(menuName)}}
            ]))[0]['_id']

            # update types
            results = list(mongo.db.types.aggregate([
                {'$match': {'_id': ObjectId(typeID)}}
            ]))

            dishes = results[0]['dishes']
            dishes.append({
                'name': str(menuName),
                'at_canteen': ObjectId(canteen_id),
                'price': float(price),
                'in_type': ObjectId(typeID),
                '_id': ObjectId(dish_id)
            })

            mongo.db.types.update_one({'_id': ObjectId(typeID)}, {'$set': {'dishes': dishes}})

            return redirect('/canteen_account/%s/menu' % canteen_id)
    return render_template('canteen/add_menu.html')

@app.route('/canteen_account/<canteen_id>/delete/<category>/<id>')
def delete_item(canteen_id,category,id):
    if current_user.auth_type > 1:
        return 'Not Authorized', 403
    if category == 'dishes':
        # delete from types
        target_dish = list(mongo.db.dishes.aggregate([
            {'$match': { '_id' : ObjectId(id) }},
        ]))[0]

        in_type = target_dish['in_type']
        print(target_dish)
        target_type = list(mongo.db.types.aggregate([
            {'$match': { '_id': ObjectId(in_type) }},
        ]))[0]

        dishes = target_type["dishes"]
        new_dishes = []
        for _dish in dishes:
            print(_dish)
            if _dish["_id"] == ObjectId(id):
                continue
            new_dishes.append(_dish)
        mongo.db.types.update_one({'_id': ObjectId(in_type)}, {'$set': {'dishes': new_dishes}})

        # delete from dishes
        mongo.db.dishes.delete_one({"_id": ObjectId(id)})        
    elif category == 'types':
        mongo.db.types.delete_one({"_id": ObjectId(id)})

        mongo.db.dishes.delete_many({'in_type': ObjectId(id)})

    else:
        mongo.db[category].delete_one({"_id": ObjectId(id)})
        
    return redirect('/canteen_account/%s/menu' % canteen_id)

@app.route('/canteen_account/<canteen_id>/edit/menu/<menu_id>', methods=['GET','POST'])
def edit_menu(canteen_id, menu_id):
    def isFloat(num):
        try:
            float(num)
            return True
        except:
            return False
    
    if current_user.auth_type > 1:
        return 'Not Authorized', 403

    if request.method == 'POST':
        # print(request.form)
        menuName=request.form.get('menu-name')
        price=request.form.get('price')
        if menuName == '':
            flash('Please add your menu name', category='info')
        if len(menuName) >= 300:
            flash('300 characters limit exceeded', category='warning')
        if price == '':
            flash('Please input your menu price', category='info')
        if not isFloat(price):
            flash('Please input your price as a number', category='warning')
        else:
            # update in dishes
            in_type = list(mongo.db.dishes.aggregate([
                {'$match':{'_id':ObjectId(menu_id)}}
            ]))[0]['in_type']

            mongo.db.dishes.update_one({'_id': ObjectId(menu_id)},{
                '$set':{'name': str(menuName),
                'price':float(price),
                }
            })

            # update in types
            dishes = list( mongo.db.types.aggregate([
                { '$match' : { '_id' : ObjectId(in_type) } }
            ]))[0]['dishes']

            print(dishes)
            print(1)
            
            for i in range(len(dishes)):
                # print(dishes[i])
                if dishes[i]['_id'] == ObjectId(menu_id):
                    del dishes[i]
                    break

            print(dishes)
            dishes.append({
                'name': str(menuName),
                'at_canteen': current_user.staff_of,
                'price':float(price),
                'in_type':ObjectId(in_type),
                '_id':ObjectId(menu_id)
            })
            mongo.db.types.update_one({'_id': ObjectId(in_type)}, {'$set': {'dishes': dishes}})
            return redirect('/canteen_account/%s/menu' % canteen_id)

    if request.method == 'GET':
        menu=list(mongo.db.dishes.aggregate([
            { '$match' : { '_id' : ObjectId(menu_id) } }
        ]))[0]
        
    return render_template('canteen/edit_menu.html', canteen_id=canteen_id, menu=menu)

