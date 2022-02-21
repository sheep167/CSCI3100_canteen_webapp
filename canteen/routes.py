from canteen import app, mongo
from flask import render_template, redirect, url_for, flash
from flask_login import login_user, logout_user
from .form import UserRegistrationForm, UserLoginForm
from .models import User, LoginUser
import bcrypt


@app.route('/', methods=['GET'])
def home_page():
    return render_template('home_page.html')


@app.route('/register', methods=['GET', 'POST'])
def register_page():
    form = UserRegistrationForm()

    if form.validate_on_submit():
        # print(form.email.data, form.username.data, form.password.data)
        hashed_password = bcrypt.hashpw(form.password.data.encode('utf-8'), bcrypt.gensalt())

        user_to_create = User(email=form.email.data,
                              username=form.username.data,
                              password=hashed_password)

        mongo.db.users.insert_one(user_to_create.to_json())
        return redirect(url_for('login_page'))

    if form.errors != {}:
        for error_message in form.errors.values():
            flash(error_message, category='danger')

    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login_page():
    form = UserLoginForm()
    if form.validate_on_submit():
        attempted_user = mongo.db.users.find_one({'email': form.email.data})
        if attempted_user and bcrypt.checkpw(form.password.data.encode('utf-8'), attempted_user.get('password')):
            login_user(LoginUser(attempted_user))
            flash('Successfully Logged In as: %s' % attempted_user.get('username'), category='success')
            return redirect(url_for('home_page'))
        else:
            flash('Email and Password do not match', category='danger')

    return render_template('login.html', form=form)


@app.route('/logout')
def logout_page():
    logout_user()
    flash('You have been logged out!', category='info')
    return redirect(url_for('home_page'))

