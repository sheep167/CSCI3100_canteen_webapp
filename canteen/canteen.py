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


@app.route('/canteen_account', methods=['GET', 'POST'])
def canteen_account():
    return render_template('canteen/canteen_account.html')

@app.route('/canteen_account/order', methods=['GET'])
def order_page():   
    return render_template('canteen/order.html')