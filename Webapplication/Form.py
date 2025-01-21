from wtforms import Form, StringField, PasswordField, validators

class Login(Form):
    email = StringField('Email Address:', [
        validators.DataRequired(),
        validators.Email(message="Enter a valid email address.")
    ])
    password = PasswordField('Password:', [
        validators.DataRequired(),
        validators.Length(min=6, message="Password must be at least 6 characters long.")
    ])