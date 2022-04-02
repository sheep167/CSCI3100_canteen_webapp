import datetime
from collections import Counter
from bson import ObjectId
from canteen import app, mongo, mail
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user, login_required
from .form import UserRegistrationForm, UserLoginForm
from .models import User, LoginUser
import bcrypt
from itsdangerous import URLSafeTimedSerializer, SignatureExpired
from flask_mail import Message


@app.route('/', methods=['GET'])
def home():
    # two templates are available: home.html and home2.html
    # use home.html
    return render_template('home.html')


@app.route('/user_account', methods=['GET', 'POST'])
def user_account():
    return render_template('user_account.html')


@app.route('/canteen_account', methods=['GET', 'POST'])
def canteen_account():
    return render_template('canteen_account.html')


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
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    form = UserLoginForm()
    if form.validate_on_submit():
        attempted_user = mongo.db.users.find_one({'email': form.email.data})
        # print(form.password.data.encode('utf-8'))
        # print(attempted_user.get('password'))
        # print(bcrypt.checkpw(form.password.data.encode('utf-8'), attempted_user.get('password')))
        if attempted_user and bcrypt.checkpw(form.password.data.encode('utf-8'), attempted_user.get('password')):
            if int(attempted_user.get('confirmed')) == 1:
                login_user(LoginUser(attempted_user))
                flash('Successfully Logged In as: %s' % attempted_user.get('username'), category='success')
                return redirect(url_for('home'))
            else:
                flash('Not authenticated', category='danger')
        else:
            flash('Email and Password do not match', category='danger')

    return render_template('login.html', form=form)


@app.route('/logout')
def logout_page():
    logout_user()
    flash('You have been logged out!', category='info')
    return redirect(url_for('home'))


@app.route('/confirm_email/<token>')
def confirm_email(token):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    try:
        email = serializer.loads(token, salt=app.config['SECRET_KEY'], max_age=300)
        mongo.db.users.update_one({'email': email}, {'$set': {'confirmed': 1}})
    except SignatureExpired:
        return '<h1> Token Expired </h1> '    
    return redirect(url_for('home'))


@app.route('/canteens/<_id>', methods=['GET', 'POST'])
def canteen_page(_id):
    # this must be changed to get canteen name list from mongodb
    results = mongo.db.canteens.aggregate([
        {'$match': {'_id': ObjectId(_id)}},
        {'$lookup':
            {'from': 'dishes',
             'localField': 'menu',
             'foreignField': '_id',
             'as': 'menu'}}
    ])
    canteen = list(results)

    if request.method == 'POST':
        add_to_cart(canteen_id=_id, dish_id=request.form['dish'])
        flash('Added to Cart!', category='info')
        return redirect(request.url)

    if canteen:
        canteen = canteen[0]
        if canteen.get('image_path'):
            canteen['image_path'] = canteen.get('image_path').replace(' ', '%20').replace('./canteen', '')
            for dish in canteen.get('menu'):
                dish['image_path'] = dish.get('image_path').replace(' ', '%20').replace('./canteen', '')
        else:
            canteen['image_path'] = None
        return render_template('new_canteen_page.html', canteen=canteen)
    else:
        return 'Page Not Found', 404


@app.route('/canteens')
def list_canteens():
    results = mongo.db.canteens.aggregate([
        {'$lookup':
            {'from': 'dishes',
             'localField': 'menu',
             'foreignField': '_id',
             'as': 'menu'}}
    ])
    canteens = list(results)

    for canteen in canteens:
        if canteen.get('image_path'):
            canteen['image_path'] = canteen.get('image_path').replace(' ', '%20').replace('./canteen', '')
            for dish in canteen.get('menu'):
                dish['image_path'] = dish.get('image_path').replace(' ', '%20').replace('./canteen', '')
        else:
            canteen['image_path'] = None

    return render_template('user_canteens.html', canteens=canteens)


@login_required
def add_to_cart(canteen_id, dish_id):
    cart = mongo.db.users.find_one({'_id': ObjectId(current_user._id)}, {'_id': 0, 'cart': 1}).get('cart')
    canteen_name = mongo.db.canteens.find_one({'_id': ObjectId(canteen_id)}).get('name')
    if not cart.get(canteen_name):
        cart[canteen_name] = {}
        cart[canteen_name]['cart'] = []
    cart[canteen_name]['cart'].append(ObjectId(dish_id))
    mongo.db.users.update_one({'_id': ObjectId(current_user._id)}, {'$set': {'cart': cart}})


@app.route('/cart', methods=['GET', 'POST'])
@login_required
def cart_page():
    if request.method == 'POST':
        create_order(canteen_name=request.form['canteen_name'], total_price=request.form['total_price'])
        flash('Payment successful')
        # return redirect('/')
        return redirect(request.url)

    results = mongo.db.users.find_one({'_id': ObjectId(current_user._id)}, {'_id': 0, 'cart': 1})

    # Count the number of each dish and retrieve the details
    cart = {}
    for canteen_name, value in results.get('cart').items():
        cart[canteen_name] = {}
        cart[canteen_name]['cart'] = []
        counter = Counter(value.get('cart'))
        for dish_id, count in counter.items():
            dish_obj = mongo.db.dishes.find_one({'_id': ObjectId(dish_id)})
            dish_obj['count'] = count
            cart[canteen_name]['cart'].append(dish_obj)

    # Replace the image_path
    # Calculate the total_price for each canteen
    for canteen_name in cart.keys():
        total_price = 0
        cart_array = cart[canteen_name]['cart']
        for dish in cart_array:
            if dish.get('image_path'):
                dish['image_path'] = dish.get('image_path').replace(' ', '%20').replace('./canteen', '')
            total_price += dish.get('price') * dish.get('count')
        cart[canteen_name]['total_price'] = total_price
    return render_template('checkout_page.html', cart=cart)


@login_required
def create_order(canteen_name, total_price):
    total_price = float(total_price)
    canteen_id = mongo.db.canteens.find_one({'name': canteen_name}).get('_id')
    cart = mongo.db.users.find_one({'_id': ObjectId(current_user._id)}, {'_id': 0, 'cart': 1}).get('cart')
    # print(cart)
    target = cart.pop(canteen_name)
    # print(target)
    order = {
        'at_time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'order_status': 'waiting',
        'dishes': target.get('cart'),
        'total_price': total_price,
        'at_canteen': ObjectId(canteen_id),
        'by_user': ObjectId(current_user._id)
    }
    mongo.db.orders.insert_one(order)
    mongo.db.users.update_one({'_id': ObjectId(current_user._id)}, {'$set': {'cart': cart}})
    mongo.db.users.update_one({'_id': ObjectId(current_user._id)}, {'$inc': {'balance': -total_price}})
