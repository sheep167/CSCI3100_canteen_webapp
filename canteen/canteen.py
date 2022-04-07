import datetime
from nis import match
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
from flask_wtf import FlaskForm # 1.
from wtforms import StringField # 2.
from wtforms.validators import DataRequired # 3.

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

@app.route('/canteen_account', methods=['GET', 'POST'])
def canteen_account():
    return render_template('canteen/canteen_account.html')

@app.route('/canteen_account/order', methods=['GET', 'POST'])
@login_required
def order_page():
    if current_user.auth_type != 2:
        return 'Not Authorized', 403
    if request.method == 'GET':
        results = mongo.db.orders.aggregate([
        { '$match' : { 'at_canteen' : "UC Canteen"} } # edit!!!
        ])
        orders = list(results)
    return render_template('canteen/order.html', orders = orders)

@app.route('/canteen_account/menu', methods=['GET', 'POST'])
@login_required
def menu_page():
    if current_user.auth_type != 2:
        return 'Not Authorized', 403
    if request.method == 'GET':
        results = mongo.db.sets.aggregate([
        { '$match' : { 'at_canteen' : "UC Canteen"} } # edit!!!
        ])
        sets = list(results)
        results = mongo.db.types.aggregate([
        { '$match' : { 'at_canteen' : "UC Canteen"} } # edit!!!
        ])
        types = list(results)
    return render_template('canteen/menu.html', sets = sets, types = types)

@app.route('/add/set', methods=['GET', 'POST'])
@login_required
def add_set():
    if current_user.auth_type != 2:
        return 'Not Authorized', 403
    if request.method == 'GET':
        results = mongo.db.type.aggregate([
        { '$match' : { 'at_canteen' : ObjectId(current_user._id)} }
        ])
        types = list(results)

    if request.method == 'POST':
        name = request.form.get("set_name")
    return render_template('canteen/order.html', types = types)
    
    
@app.route('/canteen_account/add_type', methods=['GET', 'POST'])
@login_required
def add_type():
    # canteen = mongo.db.canteens.find_one({'_id': ObjectId(canteen_id)})
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
                'at_canteen': None,
                'dishes':None
            })
        return redirect('/canteen_account/menu')
    return render_template('canteen/add_type.html')

@app.route('/canteen_account/add_set')
def add_set1():
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

