import datetime
from collections import Counter
import re
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
import os

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
            time = order['at_time']
            duration = datetime.datetime.now() - time
            duration_in_s = duration.total_seconds()
            if order['order_status'] == 'finished':
                pass
            elif duration_in_s >= 15 * 60 :
                order['order_status'] = 'rush'
            elif duration_in_s >= 5 * 60 :
                order['order_status'] = 'normal'
            mongo.db.orders.update_one({'_id': ObjectId(order['_id'])}, {'$set': {'order_status' : order['order_status']}})

            counter = Counter(order['dishes'])
            counted_dishes = []
            for dish_id, count in counter.items():
                results = mongo.db.dishes.aggregate([
                    {'$match': {'_id': ObjectId(dish_id)}}  # edit!!!
                ])
                dish = list(results)
                counted_dishes.append([dish[0]['name'],count])

            order['dishes'] = counted_dishes

    return render_template('canteen/order.html', orders=orders)

@app.route('/canteen_account/<canteen_id>/menu', methods=['GET', 'POST'])
@login_required
def menu_page(canteen_id, invalid_delete=''):
    if current_user.auth_type > 1:
        return 'Not Authorized', 403

    if request.method == 'POST':
        set_name=request.form.get('active-set')

        _set=list(mongo.db.sets.aggregate([
            {'$match':{'name':set_name}}
        ]))[0]

        mongo.db.canteens.update_one({'_id': ObjectId(canteen_id)}, {'$set': {'active_set': _set['_id']}})

        return redirect('/canteen_account/%s/menu' % canteen_id)    

    if request.method == 'GET':
        if invalid_delete == 'sets':
            flash('You cannot delete current active set', category='warning')
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

        active_set=list(mongo.db.canteens.aggregate([
            {'$match': {'_id': ObjectId(canteen_id)}}
        ]))[0]['active_set']

    return render_template('canteen/menu.html', canteen_id=canteen_id, sets=sets, types=types, active_set=active_set)

@app.route('/canteen_account/finish/<order_id>', methods=['GET', 'POST'])
@login_required
def finish_order(order_id):
    order = mongo.db.orders.aggregate([
            {'$match': {'_id': ObjectId(order_id)}}
        ])
    order = list(order)
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
            
            mongo.db.sets.insert_one({
                'name': _set_name,
                'at_canteen': ObjectId(canteen_id),
                'types': _dish_dict,
            })
            return redirect('/canteen_account/%s/menu' % canteen_id)

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
            sets=list(mongo.db.sets.aggregate([]))

            for _set in sets:
                _set['types'][typename]=[]
                mongo.db.sets.update_one({'_id': ObjectId(_set['_id'])}, {'$set': {'types': _set['types']}})

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

    if request.method == 'POST':
        _set_name = request.form.get('set-name')
        if _set_name == '':
            flash('Please add your set name', category='info')
        else:
            _dish_dict = {}
            types = list(mongo.db.types.aggregate([
                {'$match': {'at_canteen': ObjectId(canteen_id)}}
            ]))

            dish_only=[]
            for _type in types:
                checkboxAns = request.form.getlist(_type['name'])
                _dish_dict[_type['name']] = checkboxAns

                for dish_name in checkboxAns:
                    dish_id=list(mongo.db.dishes.aggregate([
                        {'$match':{'name': dish_name}}
                    ]))[0]['_id']

                    dish_only.append(dish_id)
            mongo.db.sets.update_one({'_id': ObjectId(set_id)}, {'$set': {'types': _dish_dict, 'name':_set_name} })

            mongo.db.canteens.update_one({'_id': ObjectId(canteen_id)}, {'$set': {'menu': dish_only} })

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

    def save_image():
        folder_path = './canteen/static/image/menu'
        os.makedirs(folder_path, exist_ok=True)
        save_path = os.path.join(folder_path, filename).replace('\\', '/')
        file.save(save_path)
        return save_path

    if request.method == 'POST':

        menuName = request.form.get('menu-name')
        price = request.form.get('price')
        ingredients = re.split(", |," ,request.form.get('ingredients'))
        if menuName == '':
            flash('Please add your menu name', category='info')
        if len(menuName) >= 300:
            flash('300 characters limit exceeded', category='warning')
        if price == '':
            flash('Please input your menu price', category='info')
        elif not isFloat(price):
            flash('Please input your price as a number', category='warning')
        elif int(price) <= 0:
            flash('Please input your price as a positive number', category='warning')
        else:

            # update dishes
            mongo.db.dishes.insert_one({
                'name': str(menuName),
                'at_canteen': ObjectId(canteen_id),
                'price': float(price),
                'in_type': ObjectId(typeID),
                'ingredients':ingredients
            })

            dish_id = list(mongo.db.dishes.aggregate([
                {'$match': {'name':str(menuName)}}
            ]))[0]['_id']

            user = mongo.db.users.find_one({'_id': ObjectId(current_user._id)})
            if request.files:
                file = request.files['file']
                if file.filename != '':
                    filename = secure_filename(file.filename)
                    if '.' in filename and filename.rsplit('.', 1)[1].lower() in ('jpg', 'jpeg', 'png'):
                        filename = str(dish_id) + '.' + filename.rsplit('.', 1)[1].lower()
                        image_path = save_image()
                        mongo.db.dishes.update_one({'_id': ObjectId(dish_id)}, {'$set': {'image_path': image_path}})
                    else:
                        flash('File not supported', category='warning')
                        return redirect(request.url)

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
                '_id': ObjectId(dish_id),
                'ingredients':ingredients
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

        # delete from sets
        sets=list(mongo.db.sets.aggregate([
            {'$match': {'at_canteen':ObjectId(canteen_id)}}
        ]))
        for _set in sets:
            dish_in_set=_set['types']
            for _type in dish_in_set:
                if target_dish['name'] in dish_in_set[_type]:
                    dish_in_set[_type].remove(target_dish['name'])
            mongo.db.sets.update_one({'_id': ObjectId(_set['_id'])}, {'$set': {'types': dish_in_set}})

        # delete from dishes
        mongo.db.dishes.delete_one({"_id": ObjectId(id)})
    elif category == 'types':
        target_type_name=list(mongo.db.types.aggregate([
            {'$match':{'_id':ObjectId(id)}}
        ]))[0]['name']
        sets = list(mongo.db.sets.aggregate([]))
        for _set in sets:
            types_in_set = _set['types']
            del types_in_set[target_type_name]
            mongo.db.sets.update_one({'_id': ObjectId(_set['_id'])}, {'$set': {'types': types_in_set}})

        mongo.db.types.delete_one({"_id": ObjectId(id)})
        mongo.db.dishes.delete_many({'in_type': ObjectId(id)})
    elif category == 'sets':
        canteen=list(mongo.db.canteens.aggregate([
            {'$match':{'_id': ObjectId(canteen_id)}}
        ]))[0]
        if 'active_set' in canteen:
            active_set=canteen['active_set']
        else:
            active_set=''
        if ObjectId(id) == ObjectId(active_set):
            return menu_page(canteen_id, invalid_delete='sets')
        else:
            mongo.db[category].delete_one({"_id": ObjectId(id)})
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
    
    def save_image():
        folder_path = './canteen/static/image/menu'
        os.makedirs(folder_path, exist_ok=True)
        save_path = os.path.join(folder_path, filename).replace('\\', '/')
        file.save(save_path)
        return save_path
    
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
        if float(price) <= 0:
            flash('Please input a positive price', category='warning')
        elif not isFloat(price):
            flash('Please input your price as a number', category='warning')
        else:
            if request.files:
                file = request.files['file']
                if file.filename != '':
                    filename = secure_filename(file.filename)
                    if '.' in filename and filename.rsplit('.', 1)[1].lower() in ('jpg', 'jpeg', 'png'):
                        filename = str(menu_id) + '.' + filename.rsplit('.', 1)[1].lower()
                        image = save_image()
                        print(image)
                    else:
                        flash('File not supported', category='warning')
                        return redirect(request.url)

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

