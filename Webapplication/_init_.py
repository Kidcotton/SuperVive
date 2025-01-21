from flask import Flask, render_template, request, redirect, url_for, flash, session
from createTradeIn import CreateTradeInForm
import shelve, tradein
from SignupForm import SignUpForm
from Form import Login
from User import User
from wtforms import Form, StringField, PasswordField, validators



app = Flask(__name__)


@app.route('/')
def home():
    return render_template("home.html")


@app.route('/details')
def details():
    users_dict = {}
    db = shelve.open('user.db', 'r')
    users_dict = db['Users']

    db.close()

    users_list = []
    for key in users_dict:
        user = users_dict.get(key)

        component = user.get_types_component()
        condition = user.get_condition()

        user.discount = discount(component, condition)

        users_list.append(user)

        return render_template('details.html', users_list=users_list)


@app.route('/createTradeIn', methods=['GET','POST'])
def create_tradein():
    create_tradeIn_form = CreateTradeInForm(request.form)
    if request.method == 'POST' and create_tradeIn_form.validate():
        users_dict ={}
        db = shelve.open('user.db','c')

        try:
            users_dict =db['Users']
        except:
            print("Error In Retrieving Users From user.db")

        user = tradein.tradein(create_tradeIn_form.computer_component.data,create_tradeIn_form.part_types.data,create_tradeIn_form.condition.data,create_tradeIn_form.remarks.data)
        users_dict[user.get_trade_in()] = user
        db['Users']= users_dict


        db.close()

        return redirect(url_for('details'))
    return render_template('createTradeIn.html',form=create_tradeIn_form)

@app.route('/retrieveTradeIn')
def retrieve_TradeIn():
    users_dict = {}
    db = shelve.open('user.db','r')
    users_dict = db['Users']
    db.close()

    users_list = []
    for key in users_dict:
        user=users_dict.get(key)
        users_list.append(user)
    return render_template('retrieveTradeIn.html',count=len(users_list),users_list=users_list)

@app.route('/updateUser/<int:id>/',methods=['GET','POST'])
def update_user(id):
    update_user_form = CreateTradeInForm(request.form)
    if request.method =='POST' and update_user_form.validate():
        users_dict = {}
        db = shelve.open('user.db','w')
        users_dict =db['Users']

        user = users_dict.get(id)
        user.set_pc_component(update_user_form.computer_component.data)
        user.set_types_component(update_user_form.part_types.data)
        user.set_condition(update_user_form.condition.data)
        user.set_remarks(update_user_form.remarks.data)

        db['Users'] = users_dict
        db.close()

        return redirect(url_for('retrieve_TradeIn'))
    else:
        users_dict = {}
        db = shelve.open('user.db','r')
        users_dict = db['Users']
        db.close()

        user = users_dict.get(id)
        update_user_form.computer_component.data = user.get_pc_component()
        update_user_form.part_types.data = user.get_types_component()
        update_user_form.condition.data = user.get_condition()
        update_user_form.remarks.data = user.get_remarks()

        return render_template('updateUser.html',form=update_user_form)

@app.route('/deleteTradein/<int:id>',methods=['POST'])
def delete_tradein(id):
    users_dict = {}
    db = shelve.open('user.db','w')
    users_dict = db['Users']

    users_dict.pop(id)

    db['Users'] = users_dict
    db.close()

    return redirect(url_for('retrieve_TradeIn'))


def discount(component, condition):
    discounts = {
        ('3060', 'Broken'): 50,
        ('3060', 'Well-Used'): 75,
        ('3060', 'Barely-Used'): 85,
        ('3060', 'Perfect'): 100,
        ('3070', 'Broken'): 50,
        ('3070', 'Well-Used'): 100,
        ('3070', 'Barely-Used'): 85,
        ('3070', 'Perfect'): 150,
        ('3080', 'Broken'): 50,
        ('3080', 'Well-Used'): 100,
        ('3080', 'Barely-Used'): 200,
        ('3080', 'Perfect'): 250,
        ('3090', 'Broken'): 50,
        ('3090', 'Well-Used'): 200,
        ('3090', 'Barely-Used'): 300,
        ('3090', 'Perfect'): 1000,
        ('i5', 'Broken'): 10,
        ('i5', 'Well-Used'): 10,
        ('i5', 'Barely-Used'): 13,
        ('i5', 'Perfect'): 20,
        ('i7', 'Broken'): 10,
        ('i7', 'Well-Used'): 17,
        ('i7', 'Barely-Used'): 20,
        ('i7', 'Perfect'): 25,
        ('8GB', 'Broken'): 5,
        ('8GB', 'Well-Used'): 10,
        ('8GB', 'Barely-Used'): 15,
        ('8GB', 'Perfect'): 20,
        ('16GB', 'Broken'): 20,
        ('16GB', 'Well-Used'): 25,
        ('16GB', 'Barely-Used'): 27,
        ('16GB', 'Perfect'): 30,
        ('500GB', 'Broken'): 50,
        ('500GB', 'Well-Used'): 58,
        ('500GB', 'Barely-Used'): 60,
        ('500GB', 'Perfect'): 80,
        ('MB', 'Broken'): 30,
        ('MB', 'Well-Used'): 40,
        ('MB', 'Barely-Used'): 50,
        ('MB', 'Perfect'): 60,
        ('PS', 'Broken'): 25,
        ('PS', 'Well-Used'): 30,
        ('PS', 'Barely-Used'): 40,
        ('PS', 'Perfect'): 50,
    }

    discount_value = discounts.get((component, condition))

    if discount_value is None:
        return "Error in finding discount"

    return discount_value
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

print(": starting 123")
if __name__ == '__main__':
    app.run()

