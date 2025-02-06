from wtforms import Form, StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length

class Login(Form):
    email = StringField('Email Address:', [
        DataRequired(),
        Email(message="Enter a valid email address.")
    ])
    password = PasswordField('Password:', [
        DataRequired(),
        Length(min=6, message="Password must be at least 6 characters long.")
    ])

class AdminSignUpForm(Form):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password', message="Passwords must match.")])
    submit = SubmitField('Sign Up')
