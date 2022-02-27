from canteen import app, mongo, mail
from flask import render_template, redirect, url_for, flash
from flask_login import login_user, logout_user
from .form import UserRegistrationForm, UserLoginForm
from .models import User, LoginUser
import bcrypt
from itsdangerous import URLSafeTimedSerializer, SignatureExpired
from flask_mail import Message


@app.route('/', methods=['GET'])
def home_page():
    return render_template('home_page.html')


def generate_confirmation_token(email):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    return serializer.dumps(email, salt=app.config['SECRET_KEY'])


@app.route('/register', methods=['GET', 'POST'])
def register_page():
    form = UserRegistrationForm()

    if form.validate_on_submit():
        # print(form.email.data, form.username.data, form.password.data)
        hashed_password = bcrypt.hashpw(form.password.data.encode('utf-8'), bcrypt.gensalt())

        user_to_create = User(email=form.email.data,
                              username=form.username.data,
                              password=hashed_password)

        token = generate_confirmation_token(form.email.data)

        msg = Message('Verification Email', recipients=[form.email.data])
        msg.body = 'Go here to for verification. http://localhost:5000/confirm_email/%s' % token
        mail.send(msg)

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
            if attempted_user.get('confirmed') == 1:
                login_user(LoginUser(attempted_user))
                flash('Successfully Logged In as: %s' % attempted_user.get('username'), category='success')
                return redirect(url_for('home_page'))
            else:
                flash('Not authenticated', category='danger')
        else:
            flash('Email and Password do not match', category='danger')

    return render_template('login.html', form=form)


@app.route('/logout')
def logout_page():
    logout_user()
    flash('You have been logged out!', category='info')
    return redirect(url_for('home_page'))


@app.route('/confirm_email/<token>')
def confirm_email(token):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    try:
        email = serializer.loads(token, salt=app.config['SECRET_KEY'], max_age=300)
        mongo.db.users.update_one({'email': email}, {'$set': {'confirmed': 1}})
    except SignatureExpired:
        return '<h1> Token Expired </h1> '
    return redirect(url_for('home_page'))


# @app.route('/test')
# def test():
#     msg = Message('Twilio SendGrid Test Email', recipients=['yiuchunto@gmail.com'])
#     msg.body = 'This is a test email!'
#     msg.html = '<p>This is a test email!</p>'
#     mail.send(msg)
#     return 'ok'
