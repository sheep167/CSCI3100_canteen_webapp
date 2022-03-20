from canteen import app, mongo
from flask import render_template, request, redirect, flash, url_for
from flask_login import current_user
from .form import DataEditForm
import json
from json import JSONDecodeError
from bson import ObjectId
import bcrypt


class ValidationError(Exception):
    pass


@app.route('/overview/<category>')
def admin_user_page(category):
    if current_user.is_authenticated:
        # print(current_user.user_json)
        if current_user.auth_type != 0:
            return 'Not Authorized', 403
    else:
        return redirect('/login')

    if category == 'users':
        users = list(mongo.db.users.find())
        return render_template('admin_users.html', users=users)
    elif category == 'canteens':
        canteens = list(mongo.db.canteens.find())
        return render_template('admin_canteens.html', canteens=canteens)
    elif category == 'comments':
        comments = list(mongo.db.comments.find())
        return render_template('admin_comments.html', comments=comments)


@app.route('/add/<category>', methods=['GET', 'POST'])
def add_data_page(category):
    if current_user.is_authenticated:
        # print(current_user.user_json)
        if current_user.auth_type != 0:
            return 'Not Authorized', 403
    else:
        return redirect('/login')

    form = DataEditForm()
    mongo_col = mongo.db[category]

    if request.method == 'GET':
        if category == 'users':
            form.text.data = json.dumps({'email': 'str', 'password': 'str', 'username': 'str', 'auth_type': 'int', 'confirmed': 'int', 'balance': 'float'}, indent=4)
        elif category == 'canteens':
            form.text.data = json.dumps({'name': 'str', 'longitude': 'float', 'latitude': 'float', 'open_at': 'str', 'close_at': 'str', 'capacity': 'int', 'menu':'list'}, indent=4)
        elif category == 'dishes':
            form.text.data = json.dumps({'name': 'str', 'in_canteen': 'object_id', 'price': 'float', 'ingredients': 'List[str]','rating': 'int','image_file_name': 'str'}, indent=4)
        elif category == 'comments':
            form.text.data = json.dumps({'posted_time': 'str', 'posted_by_user': 'object_id', 'posted_on_canteen': 'object_id', 'rating': 'int', 'paragraph': 'str'}, indent=4)
        elif category == 'orders':
            form.text.data = json.dumps({'created_time': 'str', 'created_by_user': 'object_id','created_at_canteen': 'object_id','food': 'List[object_id]', 'total_price': 'float', 'order_status': 'str'}, indent=4)
        else:
            return 'Not Found', 404

    if request.method == 'POST':
        try:
            data = json.loads(form.text.data)

            if category == 'users':
                if mongo_col.find_one({'$or': [{'email': data.get('email')}, {'username': data.get('username')}]}):
                    raise ValidationError()

                hashed_password = bcrypt.hashpw(data.get('password').encode('utf-8'), bcrypt.gensalt())
                data['password'] = hashed_password

            mongo_col.insert_one(data)
            return redirect('/overview/%s' % category)

        except JSONDecodeError:
            flash('Cannot decode JSON. Please check and try again.', category='error')
        except ValidationError:
            flash('Duplicate keys with the database', category='error')

    return render_template('data.html', form=form, method='Add', category=category)


@app.route('/edit/<category>/<_id>', methods=['GET', 'POST'])
def edit_data_page(category, _id):
    if current_user.is_authenticated:
        # print(current_user.user_json)
        if current_user.auth_type != 0:
            return 'Not Authorized', 403
    else:
        return redirect(url_for('login'))

    form = DataEditForm()
    mongo_col = mongo.db[category]

    if request.method == 'GET':
        # print(_id)
        # print(category)
        form.text.data = json.dumps(mongo_col.find_one({'_id': ObjectId(_id)}, {'_id': 0}), indent=4, default=str)
        # print(form.text)
        
    if request.method == 'POST':
        try:
            data = json.loads(form.text.data)
            mongo_col.update_one({'_id': ObjectId(_id)}, {'$set': data})
            return redirect('/overview/%s' % category)

        except JSONDecodeError:
            flash('Cannot decode JSON. Please check and try again.', category='error')
        except ValidationError:
            flash('Duplicate keys with the database', category='error')
    return render_template('data.html', form=form, method='Edit', category=category)


@app.route('/delete/<category>/<_id>', methods=['GET', 'POST'])
def delete_data_page(category, _id):
    if current_user.is_authenticated:
        # print(current_user.user_json)
        if current_user.auth_type != 0:
            return 'Not Authorized', 403
    else:
        return redirect('/login')

    mongo_col = mongo.db[category]
    mongo_col.delete_one({'_id': ObjectId(_id)})
    flash('Item Deleted', category='info')
    return redirect('/overview/%s' % category)

