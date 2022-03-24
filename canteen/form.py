from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, FileField, SelectMultipleField
from wtforms.validators import Length, Email, DataRequired, ValidationError
from canteen import mongo


class UserRegistrationForm(FlaskForm):

    def validate_email(self, email_to_check):
        user = mongo.db.users.find_one({'email': email_to_check.data})
        if user:
            raise ValidationError('Email has already been registered')

    def validate_username(self, username_to_check):
        user = mongo.db.users.find_one({'username': username_to_check.data})
        if user:
            raise ValidationError('Username has been taken')

    email = StringField(label='Enter Email:', validators=[Email(), DataRequired()])
    username = StringField(label='Enter Username:', validators=[Length(min=2, max=20), DataRequired()])
    password = PasswordField(label='Enter Password:', validators=[Length(min=6), DataRequired()])
    submit = SubmitField(label='Register Account')


class UserLoginForm(FlaskForm):
    email = StringField(label='Enter Email:', validators=[Email(), DataRequired()])
    password = PasswordField(label='Enter Password:', validators=[Length(min=6), DataRequired()])
    submit = SubmitField(label='Sign in')


class DataEditForm(FlaskForm):
    text = TextAreaField()
    submit = SubmitField()


class DataEditFormWithImage(FlaskForm):
    text = TextAreaField()
    image = FileField()
    submit = SubmitField()


class DataEditFormWithSelect(FlaskForm):
    text = TextAreaField()
    select = SelectMultipleField()
    submit = SubmitField()
