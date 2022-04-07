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

@app.route('/canteen_account/menu', methods=['GET'])
def menu_page():
    
    return render_template('canteen/menu.html')

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

@app.route('/canteen_account/order', methods=['GET'])
def order_page():   
    return render_template('canteen/order.html')

@app.route('/canteen_account/add_type')
def add_type():
    return render_template('canteen/add_type.html')

@app.route('/canteen_account/add_set')
def add_set():
    return render_template('canteen/add_set.html')