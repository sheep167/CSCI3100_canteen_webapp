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


@app.route('/', methods=['GET'])
def home():
    results = mongo.db.canteens.aggregate([
        {'$lookup':
            {'from': 'dishes',
             'localField': 'menu',
             'foreignField': '_id',
             'as': 'menu'}}
    ])
    canteens = list(results)

    results = mongo.db.canteens.aggregate([
        {'$lookup':
            {'from': 'comments',
             'localField': '_id',
             'foreignField': 'at_canteen',
             'as': 'comments'}},
        {'$unwind': '$comments'},
        {'$group': {'_id': '$_id', 'avg_rating': {'$avg': '$comments.rating'}}}
    ])
    ratings = list(results)

    # add average_rating into canteens
    for canteen in canteens:
        for rating in ratings:
            if canteen.get('_id') == rating.get('_id'):
                canteen['avg_rating'] = rating.get('avg_rating')

    canteens_opened = []
    canteens_closed = []
    time_now = datetime.datetime.now().time()
    for canteen in canteens:
        if canteen.get('image_path'):
            canteen['image_path'] = canteen.get('image_path').replace(' ', '%20').replace('./canteen', '')
            for dish in canteen.get('menu'):
                if dish.get('image_path'):
                    dish['image_path'] = dish.get('image_path').replace(' ', '%20').replace('./canteen', '')
        else:
            canteen['image_path'] = None

        open_at = datetime.datetime.strptime(canteen.get('open_at'), '%H:%M').time()
        close_at = datetime.datetime.strptime(canteen.get('close_at'), '%H:%M').time()
        if open_at <= time_now <= close_at:
            canteens_opened.append(canteen)
        else:
            canteens_closed.append(canteen)

    return render_template('home.html', canteens_opened=canteens_opened, canteens_closed=canteens_closed)


@login_required
@app.route('/user_account', methods=['GET', 'POST'])
def user_account():
    def save_image():
        folder_path = './canteen/static/image/users_profile_pic'
        os.makedirs(folder_path, exist_ok=True)
        save_path = os.path.join(folder_path, filename).replace('\\', '/')
        file.save(save_path)
        return save_path

    if request.method == 'POST':
        user = mongo.db.users.find_one({'_id': ObjectId(current_user._id)})
        if request.files:
            file = request.files['file']
            if file.filename == '':
                flash('No selected file', category='warning')
                return redirect(request.url)
            filename = secure_filename(file.filename)
            if '.' in filename and filename.rsplit('.', 1)[1].lower() in ('jpg', 'jpeg', 'png'):
                filename = user.get('username') + '.' + filename.rsplit('.', 1)[1].lower()
                image_path = save_image()
                mongo.db.users.update_one({'_id': ObjectId(current_user._id)}, {'$set': {'image_path': image_path}})
            else:
                flash('File not supported', category='warning')
            return redirect(request.url)

        action = request.form['action']
        # Change Username
        if action == 'username':
            username = request.form.get('username', None)
            if username:
                username = request.form['username']
                if mongo.db.users.find_one({'username': username}):
                    flash('The username is already taken!', category='warning')
                    return redirect(request.url)
                mongo.db.users.update_one({'_id': ObjectId(current_user._id)}, {'$set': {'username': username}})
                flash('Username Changed!', category='info')
            else:
                flash('Enter username!', category='warning')

        # Change password
        elif action == 'password':
            old_password = request.form.get('old_password', None)
            new_password = request.form.get('new_password', None)
            if old_password and new_password:
                if bcrypt.checkpw(old_password.encode('utf-8'), user.get('password')):
                    mongo.db.users.update_one({'_id': ObjectId(user.get('_id'))}, {'$set': {'password': bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())}})
                    flash('Password Changed!', category='info')
                else:
                    flash('Wrong Password', category='warning')
            else:
                flash('Enter both password!', category='warning')

        else:
            amount = request.form.get('top-up', None)
            if amount and amount.isnumeric() and float(amount) > 0:
                amount = float(amount)
                mongo.db.users.update_one({'_id': ObjectId(user.get('_id'))}, {'$inc': {'balance': amount}})
                flash('Successful top-up!', category='info')
            else:
                flash('Positive numeric value only', category='warning')

        return redirect(request.url)

    user = mongo.db.users.find_one({'_id': ObjectId(current_user._id)})
    if user.get('image_path'):
        user['image_path'] = user.get('image_path').replace(' ', '%20').replace('./canteen', '')

    return render_template('/user/user_account.html', user=user)


def generate_confirmation_token(email):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    return serializer.dumps(email, salt=app.config['SECRET_KEY'])


@app.route('/register', methods=['GET', 'POST'])
def register_page():
    form = UserRegistrationForm()

    if form.validate_on_submit():

        hashed_password = bcrypt.hashpw(form.password.data.encode('utf-8'), bcrypt.gensalt())

        user_to_create = Users(email=form.email.data,
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

    return render_template('/user/register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    form = UserLoginForm()
    if form.validate_on_submit():
        attempted_user = mongo.db.users.find_one({'email': form.email.data})

        if attempted_user and bcrypt.checkpw(form.password.data.encode('utf-8'), attempted_user.get('password')):
            if int(attempted_user.get('confirmed')) == 1:
                login_user(LoginUsers(attempted_user))
                flash('Successfully Logged In as: %s' % attempted_user.get('username'), category='success')
                return redirect(url_for('home'))
            else:
                flash('Not authenticated', category='danger')
        else:
            flash('Email and Password do not match', category='danger')

    return render_template('/user/login.html', form=form)


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

    results = mongo.db.comments.aggregate([
        {'$match': {'at_canteen': ObjectId(_id)}},
        {'$lookup':
            {'from': 'users',
             'localField': 'by_user',
             'foreignField': '_id',
             'as': 'by_user'}},
        {'$unwind': '$by_user'},
        {'$project':
            {'at_time': 1,
             'paragraph': 1,
             'rating': 1,
             'by_user.username': 1
        }}
    ])
    comments = list(results)

    if request.method == 'POST':
        if( request.form.get('add-dish')):
            add_to_cart(canteen_id=_id, dish_id=request.form['add-dish'])
            flash('Added to Cart!', category='info')
        elif( request.form.get('remove-dish')):
            remove_from_cart(canteen_id=_id, dish_id=request.form['remove-dish'])
            flash('Removed from Cart!', category='info')
        return redirect(request.url)

    if canteen:

        #ADD CART FOR IN-PAGE CART
        cart={}
        cart_from_user = mongo.db.users.find_one({'_id': ObjectId(current_user._id)}, {'_id': 0, 'cart': 1})

        if( cart_from_user.get('cart') ):
            for canteen_name, value in cart_from_user.get('cart').items():
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

        canteen = canteen[0]
        if canteen.get('image_path'):
            canteen['image_path'] = canteen.get('image_path').replace(' ', '%20').replace('./canteen', '')
        else:
            canteen['image_path'] = None

        for dish in canteen.get('menu'):
            if dish.get('image_path'):
                dish['image_path'] = dish.get('image_path').replace(' ', '%20').replace('./canteen', '')
        
        
        return render_template('/user/new_canteen_page.html', canteen=canteen, comments=comments, cart=cart)
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
        else:
            canteen['image_path'] = None
        for dish in canteen.get('menu'):
            if dish.get('image_path'):
                dish['image_path'] = dish.get('image_path').replace(' ', '%20').replace('./canteen', '')
        

    return render_template('/user/list_canteens.html', canteens=canteens)


@login_required
def add_to_cart(canteen_id, dish_id):
    cart = mongo.db.users.find_one({'_id': ObjectId(current_user._id)}, {'_id': 0, 'cart': 1}).get('cart')
    canteen_name = mongo.db.canteens.find_one({'_id': ObjectId(canteen_id)}).get('name')
    if not cart.get(canteen_name):
        cart[canteen_name] = {}
        cart[canteen_name]['cart'] = []
    cart[canteen_name]['cart'].append(ObjectId(dish_id))
    mongo.db.users.update_one({'_id': ObjectId(current_user._id)}, {'$set': {'cart': cart}})

@login_required
def remove_from_cart(canteen_id, dish_id):
    cart = mongo.db.users.find_one({'_id': ObjectId(current_user._id)}, {'_id': 0, 'cart': 1}).get('cart')
    canteen_name = mongo.db.canteens.find_one({'_id': ObjectId(canteen_id)}).get('name')
    if not cart.get(canteen_name):
        pass
    else:
        print( cart[canteen_name]['cart'] )
        try:
            cart[canteen_name]['cart'].remove(ObjectId(dish_id))
            mongo.db.users.update_one({'_id': ObjectId(current_user._id)}, {'$set': {'cart': cart}})
        except:
            pass


@app.route('/cart', methods=['GET', 'POST'])
@login_required
def cart_page():
    if request.method == 'POST':
        if mongo.db.users.find_one({'$and': [{'_id': ObjectId(current_user._id)}, {'balance': {'$gte': float(request.form['total_price'])}}]}):
            create_order(canteen_name=request.form['canteen_name'], total_price=request.form['total_price'])
            flash('Payment successful', category='info')
        else:
            flash('Not enough balance', category='warning')
        return redirect(request.url)

    results = mongo.db.users.find_one({'_id': ObjectId(current_user._id)}, {'_id': 0, 'cart': 1})

    # Count the number of each dish and retrieve the details
    cart = {}

    #temporary fix
    if( results.get('cart') ):
        all_canteen_total = 0
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
            all_canteen_total += total_price
    return render_template('/user/checkout_page.html', cart=cart, all_canteen_total=all_canteen_total)


@login_required
def create_order(canteen_name, total_price):
    total_price = float(total_price)
    canteen_id = mongo.db.canteens.find_one({'name': canteen_name}).get('_id')
    cart = mongo.db.users.find_one({'_id': ObjectId(current_user._id)}, {'_id': 0, 'cart': 1}).get('cart')
    target = cart.pop(canteen_name)

    order = {
        'at_time': datetime.datetime.now(),
        'order_status': 'waiting',
        'dishes': target.get('cart'),
        'total_price': total_price,
        'at_canteen': ObjectId(canteen_id),
        'by_user': ObjectId(current_user._id)
    }
    mongo.db.orders.insert_one(order)
    mongo.db.users.update_one({'_id': ObjectId(current_user._id)}, {'$set': {'cart': cart}})
    mongo.db.users.update_one({'_id': ObjectId(current_user._id)}, {'$inc': {'balance': -total_price}})


@login_required
@app.route('/post_comment/<canteen_id>', methods=['GET', 'POST'])
def post_comment(canteen_id):
    canteen = mongo.db.canteens.find_one({'_id': ObjectId(canteen_id)})
    paragraph = ''
    if request.method == 'POST':
        paragraph = request.form['paragraph']
        rating = request.form['rating']
        if paragraph == '':
            flash('Please type your comment', category='info')
        if len(paragraph) >= 300:
            flash('300 characters limit exceeded', category='warning')
        else:
            mongo.db.comments.insert_one({
                'at_time': datetime.datetime.now(),
                'rating': int(rating),
                'paragraph': paragraph.lstrip(),
                'at_canteen': ObjectId(canteen_id),
                'by_user': ObjectId(current_user._id)
            })
        return redirect('/canteens/%s' % canteen_id)
    return render_template('/user/post_comment.html', canteen=canteen, paragraph=paragraph)
