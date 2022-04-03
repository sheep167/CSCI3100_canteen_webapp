import datetime
import os
from canteen import app, mongo
from flask import render_template, request, redirect, flash
from flask_login import current_user, login_required
from .form import DataEditForm, DataEditFormWithImage, DataEditFormWithSelect
from werkzeug.utils import secure_filename
import json
from json import JSONDecodeError
from bson import ObjectId
import bcrypt


class ValidationError(Exception):
    pass


class NoSuchUserError(Exception):
    pass


@app.route('/reset_password/<_id>')
@login_required
def reset_password(_id):
    if current_user.auth_type != 0:
        return 'Not Authorized', 403

    mongo.db.users.update_one({'_id': ObjectId(_id)}, {'$set': {'password': bcrypt.hashpw('123456'.encode('utf-8'), bcrypt.gensalt())}})
    return redirect('/overview/users')


@app.route('/overview/<category>')
@login_required
def overview_page(category):
    if current_user.auth_type != 0:
        return 'Not Authorized', 403

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
@login_required
def add_data_page(category):
    if current_user.auth_type != 0:
        return 'Not Authorized', 403

    form = DataEditForm()
    mongo_col = mongo.db[category]

    if request.method == 'GET':
        if category == 'users':
            form.text.data = json.dumps({'email': 'str', 'password': 'str', 'username': 'str', 'auth_type': 'int', 'confirmed': 'int', 'balance': 'float'}, indent=4)
        elif category == 'canteens':
            form.text.data = json.dumps({'name': 'str', 'longitude': 'float', 'latitude': 'float', 'open_at': 'str', 'close_at': 'str', 'capacity': 'int'}, indent=4)
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
                data['cart'] = {}
                data['image_path'] = None

            elif category == 'canteens':
                data['menu'] = []

            mongo_col.insert_one(data)
            return redirect('/overview/%s' % category)

        except JSONDecodeError:
            flash('Cannot decode JSON. Please check and try again.', category='error')
        except ValidationError:
            flash('Duplicate keys with the database', category='error')

    return render_template('data.html', form=form, method='Add', category=category)


@app.route('/edit/<category>/<_id>', methods=['GET', 'POST'])
@login_required
def edit_data_page(category, _id):
    if current_user.auth_type != 0:
        return 'Not Authorized', 403

    form = DataEditForm()
    if category == 'canteens':
        form = DataEditFormWithImage()
    mongo_col = mongo.db[category]

    if request.method == 'GET':
        if category == 'users':
            form.text.data = json.dumps(mongo_col.find_one({'_id': ObjectId(_id)}, {'_id': 0, 'email': 0, 'username': 0, 'password': 0}), indent=4, default=str)
        elif category == 'canteens':
            form.text.data = json.dumps(mongo_col.find_one({'_id': ObjectId(_id)}, {'_id': 0, 'menu': 0}), indent=4, default=str)

    if request.method == 'POST':
        try:
            data = json.loads(form.text.data)
            if category == 'canteens':

                if form.image.data.filename != '':
                    filename = secure_filename(form.image.data.filename)
                    if '.' in filename and filename.rsplit('.', 1)[1].lower() in ('jpg', 'jpeg', 'png'):
                        canteen = mongo.db.canteens.find_one({'_id': ObjectId(_id)})
                        folder_path = './canteen/static/image/%s' % canteen.get('name')
                        os.makedirs(folder_path, exist_ok=True)
                        save_path = os.path.join(folder_path, filename).replace('\\', '/')
                        form.image.data.save(save_path)
                        data['image_path'] = save_path
                    else:
                        raise ValidationError()
                else:
                    data['image_path'] = None

            mongo_col.update_one({'_id': ObjectId(_id)}, {'$set': data})
            return redirect('/overview/%s' % category)

        except JSONDecodeError:
            flash('Cannot decode JSON. Please check and try again.', category='error')

    if category == 'canteens':
        return render_template('data_with_image.html', form=form, method='Edit', category=category)
    return render_template('data.html', form=form, method='Edit', category=category)


@app.route('/delete/<category>/<_id>', methods=['GET', 'POST'])
@login_required
def delete_data_page(category, _id):
    if current_user.auth_type != 0:
        return 'Not Authorized', 403

    mongo_col = mongo.db[category]
    mongo_col.delete_one({'_id': ObjectId(_id)})
    flash('Item Deleted', category='info')
    return redirect('/overview/%s' % category)


@app.route('/overview/canteens/<canteen_id>/<category>')
@login_required
def overview_canteens_dishes(canteen_id, category):
    if current_user.auth_type != 0:
        return 'Not Authorized', 403

    if category == 'dishes':
        canteen = mongo.db.canteens.find_one({'_id': ObjectId(canteen_id)})

        results = mongo.db.dishes.aggregate([
            {'$match': {'at_canteen': ObjectId(canteen_id)}},
            {'$lookup':
                {'from': 'canteens',
                 'localField': 'at_canteen',
                 'foreignField': '_id',
                 'as': 'at_canteen'}},
            {'$set': {'at_canteen': {'$arrayElemAt': ['$at_canteen', 0]}}},
            {'$set': {'at_canteen': '$at_canteen.name'}}
        ])

        dishes = list(results)
        for dish in dishes:
            if dish.get('image_path'):
                dish['image_path'] = dish.get('image_path').replace(' ', '%20').replace('./canteen', '')
            else:
                dish['image_path'] = None

        return render_template('admin_dishes.html', canteen=canteen, dishes=dishes)

    elif category == 'comments':

        canteen = mongo.db.canteens.find_one({'_id': ObjectId(canteen_id)})
        results = mongo.db.comments.aggregate([
            {'$match': {'at_canteen': ObjectId(canteen_id)}},
            {'$lookup':
                {'from': 'users',
                 'localField': 'by_user',
                 'foreignField': '_id',
                 'as': 'by_user'}},
            {'$set': {'by_user': {'$arrayElemAt': ['$by_user', 0]}}},
            {'$set': {'by_user': '$by_user.username'}}
        ])

        comments = list(results)
        return render_template('admin_comments.html', canteen=canteen, comments=comments)

    elif category == 'orders':
        canteen = mongo.db.canteens.find_one({'_id': ObjectId(canteen_id)})

        results = mongo.db.orders.aggregate([
            {'$match': {'at_canteen': ObjectId(canteen_id)}},
            {'$lookup':
                {'from': 'users',
                 'localField': 'by_user',
                 'foreignField': '_id',
                 'as': 'by_user'}},
            {'$lookup':
                {'from': 'dishes',
                 'localField': 'dishes',
                 'foreignField': '_id',
                 'as': 'dishes'}},
            {'$set': {'by_user': {'$arrayElemAt': ['$by_user', 0]}}},
            {'$set': {'by_user': '$by_user.username'}},
            {'$set': {'dishes': '$dishes.name'}}
        ])

        orders = list(results)
        for order in orders:
            order['dishes'] = ', '.join(order.get('dishes'))
        return render_template('admin_orders.html', canteen=canteen, orders=orders)


@app.route('/add/canteens/<canteen_id>/<category>', methods=['GET', 'POST'])
@login_required
def add_canteens_data(canteen_id, category):
    def save_image():
        canteen = mongo.db.canteens.find_one({'_id': ObjectId(canteen_id)})
        folder_path = './canteen/static/image/%s' % canteen.get('name')
        os.makedirs(folder_path, exist_ok=True)
        save_path = os.path.join(folder_path, filename).replace('\\', '/')
        form.image.data.save(save_path)
        data['image_path'] = save_path

    if current_user.auth_type != 0:
        return 'Not Authorized', 403

    if category == 'dishes':
        form = DataEditFormWithImage()
    elif category == 'orders':
        form = DataEditFormWithSelect()
    else:
        form = DataEditForm()

    if request.method == 'GET':
        if category == 'dishes':
            form.text.data = json.dumps({'name': 'str', 'price': 'float', 'ingredients': 'List[str]'}, indent=4)
        elif category == 'comments':
            form.text.data = json.dumps({'at_time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'username': 'str', 'rating': 'int', 'paragraph': 'str'}, indent=4)
        elif category == 'orders':
            form.text.data = json.dumps({'at_time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'username': 'str', 'order_status': 'waiting, fulfilled, unfulfilled'}, indent=4)

            dishes = mongo.db.dishes.aggregate([
                {'$match': {'at_canteen': ObjectId(canteen_id)}},
                {'$lookup':
                    {'from': 'canteens',
                     'localField': 'at_canteen',
                     'foreignField': '_id',
                     'as': 'at_canteen'}},
                {'$set': {'at_canteen': {'$arrayElemAt': ['$at_canteen', 0]}}},
                {'$set': {'at_canteen': '$at_canteen.name'}},
                {'$project': {'name': 1, '_id': 0}}
            ])
            dishes = [dish.get('name') for dish in dishes]

            form.select.choices = dishes

    if request.method == 'POST':
        try:
            data = json.loads(form.text.data)

            if category == 'dishes':

                data['at_canteen'] = ObjectId(canteen_id)

                if form.image.data.filename != '':
                    filename = secure_filename(form.image.data.filename)
                    if '.' in filename and filename.rsplit('.', 1)[1].lower() in ('jpg', 'jpeg', 'png'):
                        save_image()
                    else:
                        raise ValidationError()
                else:
                    data['image_path'] = None

            elif category == 'comments':

                data['at_canteen'] = ObjectId(canteen_id)

                user = mongo.db.users.find_one({'username': data.get('username')})
                if not user:
                    raise NoSuchUserError()
                user_id = user.get('_id')
                del data['username']
                data['by_user'] = ObjectId(user_id)

                data['at_time'] = datetime.datetime.strptime(data.get('at_time'), '%Y-%m-%d %H:%M:%S')

            elif category == 'orders':

                dishes_ids = mongo.db.dishes.aggregate([
                    {'$match': {'name': {'$in': form.select.data}}},
                    {'$project': {'_id': 1}}
                ])
                data['dishes'] = [_id.get('_id') for _id in dishes_ids]

                total_price = mongo.db.dishes.aggregate([
                    {'$match': {'name': {'$in': form.select.data}}},
                    {'$group': {'_id': 0, 'total_price': {'$sum': '$price'}}}
                ])
                total_price = list(total_price)[0].get('total_price')
                data['total_price'] = total_price

                data['at_canteen'] = ObjectId(canteen_id)

                user = mongo.db.users.find_one({'username': data.get('username')})
                if not user:
                    raise NoSuchUserError()
                user_id = user.get('_id')
                del data['username']
                data['by_user'] = ObjectId(user_id)

                data['at_time'] = datetime.datetime.strptime(data.get('at_time'), '%Y-%m-%d %H:%M:%S')

            _id = mongo.db[category].insert_one(data)

            if category == 'dishes':
                mongo.db.canteens.update_one({'_id': ObjectId(canteen_id)}, {'$push': {'menu': ObjectId(_id.inserted_id)}})

            return redirect('/overview/canteens/%s/%s' % (canteen_id, category))

        except JSONDecodeError:
            flash('Cannot decode JSON. Please check and try again.', category='error')
        except ValidationError:
            flash('Not supported file type. Only .jpg and .png are allowed', category='error')
        except NoSuchUserError:
            flash('No such user with this username', category='error')
        except ValueError:
            flash('Wrong time format', category='error')

    if category == 'dishes':
        return render_template('data_with_image.html', form=form, method='Edit')
    if category == 'orders':
        return render_template('data_with_select.html', form=form, method='Edit')
    return render_template('data.html', form=form, method='Edit')


@app.route('/edit/canteens/<canteen_id>/<category>/<_id>', methods=['GET', 'POST'])
@login_required
def edit_canteens_data(canteen_id, category, _id):

    def save_and_delete_image():
        canteen = mongo.db.canteens.find_one({'_id': ObjectId(canteen_id)})
        folder_path = './canteen/static/image/%s' % canteen.get('name')
        os.makedirs(folder_path, exist_ok=True)
        save_path = os.path.join(folder_path, filename).replace('\\', '/')
        form.image.data.save(save_path)
        old_file_name = mongo.db.dishes.find_one({'_id': ObjectId(_id)})
        old_file_name = old_file_name.get('image_path')
        if old_file_name:
            os.remove(os.path.join(folder_path, old_file_name.rsplit('/', 1)[1]).replace('\\', '/'))
        data['image_path'] = save_path

    if current_user.auth_type != 0:
        return 'Not Authorized', 403

    form = DataEditForm()
    if category == 'dishes':
        form = DataEditFormWithImage()

    if request.method == 'GET':
        if category == 'dishes':
            form.text.data = json.dumps(mongo.db.dishes.find_one({'_id': ObjectId(_id)}, {'_id': 0, 'image_path': 0, 'at_canteen': 0}), indent=4, default=str)
        elif category == 'comments':
            form.text.data = json.dumps(mongo.db.comments.find_one({'_id': ObjectId(_id)}, {'_id': 0, 'at_canteen': 0, 'by_user': 0, 'at_time': 0}), indent=4, default=str)
        # Editing the orders is not supported as this action is complicated
        # in both database query and editing them on screen

    if request.method == 'POST':
        try:
            data = json.loads(form.text.data)

            if category == 'dishes':
                if form.image.data.filename != '':
                    filename = secure_filename(form.image.data.filename)
                    if '.' in filename and filename.rsplit('.', 1)[1].lower() in ('jpg', 'jpeg', 'png'):
                        save_and_delete_image()
                    else:
                        raise ValidationError()

            mongo.db[category].update_one({'_id': ObjectId(_id)}, {'$set': data})
            return redirect('/overview/canteens/%s/%s' % (canteen_id, category))

        except JSONDecodeError:
            flash('Cannot decode JSON. Please check and try again.', category='error')
        except ValidationError:
            flash('Not supported file type. Only .jpg and .png are allowed', category='error')

    if category == 'dishes':
        return render_template('data_with_image.html', form=form, method='Edit')
    return render_template('data.html', form=form, method='Edit')


@app.route('/delete/canteens/<canteen_id>/<category>/<_id>', methods=['GET', 'POST'])
@login_required
def delete_canteens_data(canteen_id, category, _id):

    def delete_image():
        canteen = mongo.db.canteens.find_one({'_id': ObjectId(canteen_id)})
        folder_path = './canteen/static/image/%s' % canteen.get('name')
        old_file_name = mongo.db.dishes.find_one({'_id': ObjectId(_id)})
        old_file_name = old_file_name.get('image_path')
        if old_file_name:
            os.remove(os.path.join(folder_path, old_file_name.rsplit('/', 1)[1]).replace('\\', '/'))

    if current_user.auth_type != 0:
        return 'Not Authorized', 403

    if category == 'dishes':
        # Delete image only if there is no entry sharing the same image
        image_path = mongo.db.dishes.find_one({'_id': ObjectId(_id)}, {'image_path': 1}).get('image_path')
        if mongo.db.dishes.count_documents({'image_path': image_path}) == 1:
            delete_image()
        mongo.db.canteens.update_one({'_id': ObjectId(canteen_id)}, {'$pull': {'menu': ObjectId(_id)}})

    mongo.db[category].delete_one({'_id': ObjectId(_id)})
    flash('Item Deleted', category='info')
    return redirect('/overview/canteens/%s/%s' % (canteen_id, category))
