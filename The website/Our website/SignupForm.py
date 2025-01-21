from wtforms import Form, StringField, PasswordField, validators

class SignUpForm(Form):
    email = StringField(
        'Email Address:',
        validators=[
            validators.DataRequired(message="Email address is required."),
            validators.Email(message="Enter a valid email address."),
        ]
    )
    password = PasswordField(
        'Password:',
        validators=[
            validators.DataRequired(message="Password is required."),
            validators.Length(min=6, message="Password must be at least 6 characters long."),
        ]
    )
    confirm_password = PasswordField(
        'Confirm Password:',
        validators=[
            validators.DataRequired(message="Please confirm your password."),
            validators.EqualTo('password', message="Passwords must match."),
        ]
    )