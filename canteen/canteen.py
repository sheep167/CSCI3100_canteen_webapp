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
from flask_wtf import FlaskForm # 1.
from wtforms import StringField # 2.
from wtforms.validators import DataRequired # 3.
import threading
import time
from turbo_flask import turbo


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
    if current_user.auth_type != 2:
        return 'Not Authorized', 403
    if request.method == 'GET':
        results = mongo.db.orders.aggregate([
        { '$match' : { 'at_canteen' : ObjectId(canteen_id) }} # edit!!!
        ])
        orders = list(results)
    return render_template('canteen/order.html', orders = orders)


@app.route('/canteen_account/<canteen_id>/menu', methods=['GET', 'POST'])
@login_required
def menu_page(canteen_id):
    if current_user.auth_type != 2:
        return 'Not Authorized', 403
    if request.method == 'GET':
        results = mongo.db.sets.aggregate([
            { '$match' : { 'at_canteen' : ObjectId(canteen_id)} }
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
            { '$match' : { 'at_canteen' : ObjectId(canteen_id)} }
        ])
        types = list(results)
    return render_template('canteen/menu.html', canteen_id=canteen_id, sets=sets, types=types)

@app.route('/canteen_account/<canteen_id>/add/set', methods=['GET', 'POST'])
@login_required
def add_set(canteen_id):
    if current_user.auth_type != 2:
        return 'Not Authorized', 403

    if request.method == 'POST':
        _set_name = request.form.get('set-name')

        if _set_name == '':
            flash('Please add your set name', category='info')
        else:
            _dish_dict = {}
            types = list(mongo.db.types.aggregate([
                { '$match' : { 'at_canteen' : ObjectId(canteen_id)} }
            ]))
            for _type in types:
                checkboxAns = request.form.getlist(_type['name'])
                _dish_dict[_type['name']] = checkboxAns
                 
            mongo.db.sets.insert_one({
                'name': _set_name,
                'at_canteen': ObjectId(canteen_id),
                'types': _dish_dict
            })
            return redirect('/canteen_account/%s/menu' % canteen_id)

    types=[]
    if request.method == 'GET':
        results = mongo.db.types.aggregate([
            { '$match' : { 'at_canteen' : ObjectId(canteen_id)} }
        ])
        types = list(results)

    
    return render_template('canteen/add_set.html', canteen_id=canteen_id, types=types)
    
    
@app.route('/canteen_account/<canteen_id>/add/type', methods=['GET', 'POST'])
@login_required
def add_type(canteen_id):
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

@app.route('/canteen_account/<canteen_id>/edit/set/<set_id>', methods=['GET','POST'])
def edit_set(canteen_id, set_id):
    if current_user.auth_type != 2:
        return 'Not Authorized', 403

    if request.method == 'POST':
        _set_name = request.form.get('set-name')

        if _set_name == '':
            flash('Please add your set name', category='info')
        else:
            _dish_dict = {}
            types = list(mongo.db.types.aggregate([
                { '$match' : { 'at_canteen' : ObjectId(canteen_id)} }
            ]))
            for _type in types:
                checkboxAns = request.form.getlist(_type['name'])
                _dish_dict[_type['name']] = checkboxAns
            print(checkboxAns)
            mongo.db.sets.update_one( {'_id': ObjectId(set_id)},{'$set': {'types': _dish_dict}} )

            return redirect('/canteen_account/menu')

    # types=[]
    if request.method == 'GET':
        types = list(mongo.db.types.aggregate([
            { '$match' : { 'at_canteen' : ObjectId(canteen_id)} }
        ]))
        _set = list(mongo.db.sets.aggregate([
            { '$match' : { '_id' : ObjectId(set_id)} }
        ]))[0]
        # print(_set)
        type_with_indicated=[]
        for _type in types:
            for_type=[_type['name']]
            for_type.append([])
            for dish in _type['dishes']:
                if dish['name'] in _set['types'][_type['name']]:
                    for_type[1].append([dish['name'], 1])
                else:
                    for_type[1].append([dish['name'], 0])
            type_with_indicated.append(for_type)
        print( type_with_indicated )
    return render_template('canteen/edit_set.html', canteen_id=canteen_id, type_with_indicated=type_with_indicated, _set=_set)

@app.route('/canteen_account/<canteen_id>/add/menu/<typeID>', methods=['GET','POST'])
def add_menu(canteen_id, typeID):
    def isFloat(num):
        try:
            float(num)
            return True
        except:
            return False

    if request.method == 'POST':
        menuName=request.form['menu-name']
        price=request.form['price']
        if menuName == '':
            flash('Please add your menu name', category='info')
        if len(menuName) >= 300:
            flash('300 characters limit exceeded', category='warning')
        if price == '':
            flash('Please input your menu price', category='info')
        if not isFloat(price):
            flash('Please input your price as a number', category='warning')
        else:
            mongo.db.dishes.insert_one({
                'name': str(menuName),
                'at_canteen': ObjectId(canteen_id),
                'price':float(price),
                'in_type':ObjectId(typeID)
            })

            results = list(mongo.db.types.aggregate([
                { '$match' : { '_id' : ObjectId(typeID) } }
            ]))


            dishes = results[0]['dishes']
            dishes.append({
                'name': str(menuName),
                'at_canteen': ObjectId(canteen_id),
                'price':float(price),
                'in_type':ObjectId(typeID)
            })

            mongo.db.types.update_one({'_id': ObjectId(typeID)}, {'$set': {'dishes': dishes}})

            return redirect('/canteen_account/%s/menu' % canteen_id)
    return render_template('canteen/add_menu.html', canteen_id=canteen_id)

@app.route('/canteen_account/<canteen_id>/edit/menu')
def edit_menu(canteen_id):
    return render_template('canteen/edit_menu.html', canteen_id=canteen_id)

