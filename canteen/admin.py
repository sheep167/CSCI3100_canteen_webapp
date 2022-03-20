from canteen import app, mongo
from flask import render_template, request, redirect, flash
from flask_login import current_user, login_required
from .form import DataEditForm
import json
from json import JSONDecodeError
from bson import ObjectId
import bcrypt


class ValidationError(Exception):
    pass


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


@app.route('/overview/canteens/<canteen_id>/dishes')
@login_required
def overview_canteens_dishes(canteen_id):
    if current_user.auth_type != 0:
        return 'Not Authorized', 403
    mongo_col = mongo.db['dishes']
    results = mongo_col.aggregate([
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
    return render_template('admin_dishes.html', canteen_id=canteen_id, dishes=dishes)


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
        elif category == 'dishes':
            form.text.data = json.dumps({'name': 'str', 'in_canteen': 'object_id', 'price': 'float', 'ingredients': 'List[str]', 'rating': 'int', 'image_file_name': 'str'}, indent=4)
        elif category == 'comments':
            form.text.data = json.dumps({'posted_time': 'str', 'posted_by_user': 'object_id', 'posted_on_canteen': 'object_id', 'rating': 'int', 'paragraph': 'str'}, indent=4)
        elif category == 'orders':
            form.text.data = json.dumps({'created_time': 'str', 'created_by_user': 'object_id', 'created_at_canteen': 'object_id', 'food': 'List[object_id]', 'total_price': 'float', 'order_status': 'str'}, indent=4)
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
@login_required
def delete_data_page(category, _id):
    if current_user.auth_type != 0:
        return 'Not Authorized', 403

    mongo_col = mongo.db[category]
    mongo_col.delete_one({'_id': ObjectId(_id)})
    flash('Item Deleted', category='info')
    return redirect('/overview/%s' % category)

