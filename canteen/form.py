from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, FileField, SelectMultipleField
from wtforms.validators import Length, Email, DataRequired, ValidationError
from canteen import mongo


# Form used for user registration
class UserRegistrationForm(FlaskForm):
    # Validate functions are named as validate_variable
    def validate_email(self, email_to_check):
        user = mongo.db.users.find_one({'email': email_to_check.data})
        if user:
            raise ValidationError('Email has already been registered')

    def validate_username(self, username_to_check):
        user = mongo.db.users.find_one({'username': username_to_check.data})
        if user:
            raise ValidationError('Username has been taken')

    # Specify the input field
    # Use pre-made validators
    email = StringField(label='Enter Email:', validators=[Email(), DataRequired()])
    username = StringField(label='Enter Username:', validators=[Length(min=2, max=20), DataRequired()])
    password = PasswordField(label='Enter Password:', validators=[Length(min=6), DataRequired()])
    submit = SubmitField(label='Register Account')


# Form used to handle user login
class UserLoginForm(FlaskForm):
    email = StringField(label='Enter Email:', validators=[Email(), DataRequired()])
    password = PasswordField(label='Enter Password:', validators=[Length(min=6), DataRequired()])
    submit = SubmitField(label='Sign in')


# Form used for admin to create and edit data
# No validators because of flexibility.
# This form is used for many categories
class DataEditForm(FlaskForm):
    text = TextAreaField()
    submit = SubmitField()


# Form used for admin with image selection
class DataEditFormWithImage(FlaskForm):
    text = TextAreaField()
    image = FileField()
    submit = SubmitField()


# Form used for admin with dropdown menu selection
class DataEditFormWithSelect(FlaskForm):
    text = TextAreaField()
    select = SelectMultipleField()
    submit = SubmitField()

