import datetime
import os
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

@app.route('/canteen_account/menu', methods=['GET'])
def menu_page():
    
    return render_template('canteen/menu.html')


@app.route('/canteen_account', methods=['GET', 'POST'])
def canteen_account():
    return render_template('canteen/canteen_account.html')

@app.route('/canteen_account/order', methods=['GET'])
def order_page():   
    return render_template('canteen/order.html')

@app.route('/canteen_site/add/<category>')
@login_required
def add_data(category):
    if current_user.auth_type != 2:
        return 'Not Authorized', 403

    form = DataEditForm()

    if request.method == 'GET':
        if category == 'users':
            form.text.data = json.dumps(Users.template_object(), indent=4)
        elif category == 'canteens':
            form.text.data = json.dumps(Canteens.template_object(), indent=4)
        else:
            return 'Not Found', 404

    if request.method == 'POST':
        try:
            data = json.loads(form.text.data)

            if category == 'users':
                if mongo.db.users.find_one({'$or': [{'email': data.get('email')}, {'username': data.get('username')}]}):
                    raise ValidationError()

                hashed_password = bcrypt.hashpw(data.get('password').encode('utf-8'), bcrypt.gensalt())

                user_to_insert = Users(email=data.get('email'),
                                       password=hashed_password,
                                       username=data.get('username')
                                       )

                mongo.db.users.insert_one(user_to_insert.to_json())

            elif category == 'canteens':
                if mongo.db.canteens.find_one({'name': data.get('name')}):
                    raise ValidationError()

                canteen_to_insert = Canteens(name=data.get('name'),
                                             longitude=data.get('longitude'),
                                             latitude=data.get('latitude'),
                                             open_at=data.get('open_at'),
                                             close_at=data.get('close_at'),
                                             capacity=data.get('capacity'))

                mongo.db.canteens.insert_one(canteen_to_insert.to_json())

            return redirect('/overview/%s' % category)

        except JSONDecodeError:
            flash('Cannot decode JSON. Please check and try again.', category='error')
        except ValidationError:
            flash('Duplicate keys with the database', category='error')
        except TypeError and ValueError:
            flash('Wrong type of values', category='error')

    return render_template('admin/data.html', form=form, method='Add', category=category)
@app.route('/canteen_account/add_type')
def add_type():
    return render_template('canteen/add_type.html')

@app.route('/canteen_account/add_set')
def add_set():
    return render_template('canteen/add_set.html')

@app.route('/canteen_account/edit_set')
def edit_set():
    return render_template('canteen/edit_set.html')

@app.route('/canteen_account/add_menu')
def add_menu():
    return render_template('canteen/add_menu.html')

@app.route('/canteen_account/edit_menu')
def edit_menu():
    return render_template('canteen/edit_menu.html')

