from canteen import app, mongo
from flask import render_template, request, redirect, flash
from flask_login import current_user
from .form import DataEditForm
import json
from json import JSONDecodeError
from bson import ObjectId
import bcrypt


class ValidationError(Exception):
    pass


@app.route('/overview/users')
def admin_user_page():
    if current_user.user_json.get('auth_type') != 0:
        return 'Not Authorized', 403
    users = list(mongo.db.users.find())
    return render_template('admin_users.html', users=users)


@app.route('/add/<category>', methods=['GET', 'POST'])
def add_data_page(category):
    form = DataEditForm()
    mongo_col = mongo.db[category]

    if request.method == 'GET':
        if category == 'users':
            form.text.data = json.dumps({'email': 'str', 'password': 'str', 'username': 'str', 'auth_type': 'int', 'confirmed': 'int', 'balance': 'float'}, indent=4)

    if request.method == 'POST':
        try:
            data = json.loads(form.text.data)

            if mongo_col.find_one({'$or': [{'email': data.get('email')}, {'username': data.get('username')}]}):
                raise ValidationError()

            hashed_password = bcrypt.hashpw(data.get('password').encode('utf-8'), bcrypt.gensalt())
            data['password'] = hashed_password

            mongo_col.insert_one(data)
            return redirect('/overview/%s' % category)

        except JSONDecodeError:
            flash('Cannot decode JSON. Please check and try again.', category='error')
        except ValidationError:
            flash('Duplicate keys with the database', category='error')

    return render_template('data.html', form=form)


@app.route('/edit/<category>/<_id>', methods=['GET', 'POST'])
def edit_data_page(category, _id):
    form = DataEditForm()
    mongo_col = mongo.db[category]

    if request.method == 'GET':
        if category == 'users':
            form.text.data = json.dumps(mongo_col.find_one({'_id': ObjectId(_id)}, {'_id': 0}), indent=4, default=str)

    if request.method == 'POST':
        try:
            data = json.loads(form.text.data)
            mongo_col.update_one({'_id': ObjectId(_id)}, {'$set': data})
            return redirect('/overview/%s' % category)

        except JSONDecodeError:
            flash('Cannot decode JSON. Please check and try again.', category='error')
        except ValidationError:
            flash('Duplicate keys with the database', category='error')

    return render_template('data.html', form=form)


@app.route('/delete/<category>/<_id>', methods=['GET', 'POST'])
def delete_data_page(category, _id):
    mongo_col = mongo.db[category]
    mongo_col.delete_one({'_id': ObjectId(_id)})
    flash('Item Deleted', category='info')
    return redirect('/overview/%s' % category)

