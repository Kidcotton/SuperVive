from flask import Flask, render_template, request, redirect, url_for, flash, session
from SignupForm import SignUpForm
from Form import Login
import shelve
from User import User
from wtforms import Form, StringField, PasswordField, validators


class ForgotPasswordForm(Form):
    email = StringField('Email Address:', [
        validators.DataRequired(),
        validators.Email(message="Enter a valid email address.")
    ])


class ResetPasswordForm(Form):
    new_password = PasswordField('New Password:', [
        validators.DataRequired(),
        validators.Length(min=6, message="Password must be at least 6 characters long.")
    ])
    confirm_password = PasswordField('Confirm Password:', [
        validators.DataRequired(),
        validators.EqualTo('new_password', message="Passwords must match.")
    ])


app = Flask(__name__)
app.secret_key = 'your_secret_key'


@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    form = ForgotPasswordForm(request.form)
    if request.method == 'POST' and form.validate():
        email = form.email.data

        with shelve.open('users_db') as db:
            if email in db:
                session['reset_email'] = email
                flash('Email found! You can now reset your password.', 'success')
                return redirect(url_for('reset_password'))
            else:
                flash('Email not found. Please register first.', 'error')

    return render_template('forgot_password.html', form=form)


@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    if 'reset_email' not in session:
        flash('Unauthorized access. Please use the Forgot Password form.', 'error')
        return redirect(url_for('forgot_password'))

    form = ResetPasswordForm(request.form)
    if request.method == 'POST' and form.validate():
        new_password = form.new_password.data

        with shelve.open('users_db', writeback=True) as db:
            email = session['reset_email']
            if email in db:
                db[email]['password'] = new_password 
                db.sync()  
                flash('Password reset successfully! You can now log in.', 'success')
                session.pop('reset_email')  
                return redirect(url_for('login'))
            else:
                flash('Email not found in the database. Please try again.', 'error')
                return redirect(url_for('forgot_password'))

    return render_template('reset_password.html', form=form)


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/select', methods=['GET'])
def select():
    return render_template('select.html')


@app.route('/signup_cus', methods=['GET', 'POST'])
def signup_cus():
    form = SignUpForm(request.form)
    if request.method == 'POST':
        email = form.email.data
        password = form.password.data
        confirm_password = form.confirm_password.data

        if not form.validate():
            flash("Form validation failed. Please check your input.", "error")
            return render_template('signup_cus.html', form=form)

        if password != confirm_password:
            flash("Passwords do not match. Please try again.", "error")
            return render_template('signup_cus.html', form=form)

        with shelve.open('users_db') as db:
            if email in db:
                flash('Email already exists. Please choose another one.', 'error')
                return render_template('signup_cus.html', form=form)
            else:
                db[email] = {'Email': email, 'password': password}
                flash('Registration successful! You can now log in.', 'success')
                return redirect(url_for('login'))

    return render_template('signup_cus.html', form=form)


@app.route('/login_cus', methods=['GET', 'POST'])
def login():
    form = Login(request.form)

    if request.method == 'POST' and form.validate():
        email = form.email.data
        password = form.password.data

        with shelve.open('users_db') as db:
            if email in db:
                if db[email]['password'] == password:
                    session['email'] = email
                    return redirect(url_for('home'))
                else:
                    flash('Invalid password. Please try again.', 'error')
            else:
                flash('Email not found. Please register first.', 'error')

    return render_template('login_cus.html', form=form)


@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if 'admin_logged_in' not in session:
        flash('Unauthorized access. Please log in as an admin.', 'error')
        return redirect(url_for('login'))

    users = []
    with shelve.open('users_db') as db:
        for email, details in db.items():
            users.append({'email': email, 'password': details['password']})

    return render_template('admin.html', users=users)


@app.route('/delete_user/<email>', methods=['POST'])
def delete_user(email):
    if 'admin_logged_in' not in session:
        flash('Unauthorized access. Please log in as an admin.', 'error')
        return redirect(url_for('login'))

    with shelve.open('users_db', writeback=True) as db:
        if email in db:
            del db[email]
            db.sync()
            flash(f'User {email} has been deleted.', 'success')
        else:
            flash('User not found.', 'error')

    return redirect(url_for('admin'))


@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        admin_email = request.form.get('email')
        admin_password = request.form.get('password')

        if admin_email == 'admin@example.com' and admin_password == 'adminpassword':
            session['admin_logged_in'] = True
            flash('Admin logged in successfully!', 'success')
            return redirect(url_for('admin'))
        else:
            flash('Invalid admin credentials.', 'error')

    return render_template('admin_login.html')


@app.route('/admin_logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    flash('Admin logged out successfully.', 'success')
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True)
