from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from createTradeIn import CreateTradeInForm
import shelve, tradein, User, Customer
from SignupForm import SignUpForm
from Form import Login
from Forms import CreateUserForm, CreateCustomerForm
from User import User
from wtforms import Form, StringField, PasswordField, validators

app = Flask(__name__)
app.secret_key = 'supersecretkey'

DATABASE = 'inventory.db'

@app.before_request
def initialize_cart():
    if 'cart' not in session:
        session['cart'] = []

@app.route('/prebuilds')
def prebuilds():
    return render_template('prebuild.html')

@app.route('/update_cart_quantity', methods=['POST'])
def update_cart_quantity():
    item_id = request.json.get('item_id')
    action = request.json.get('action')  

    cart = session.get('cart', [])

    for item in cart:
        if item['id'] == item_id:
            if action == 'increase':
                item['quantity'] += 1
            elif action == 'decrease' and item['quantity'] > 1:
                item['quantity'] -= 1
            break 

    session['cart'] = cart
    return jsonify(success=True, cart=cart)

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    product_id = request.form['product_id']
    print(f"Received product_id: {product_id}")

    with shelve.open(DATABASE) as db:
        print(f"Available products in database: {list(db.keys())}")

        if product_id in db:
            product = db[product_id]
            cart = session.get('cart', [])
            cart = [
                item if isinstance(item, dict) 
                else {'id': str(item), 'quantity': 1}
                for item in cart
            ]
            found_item = next((i for i in cart if i['id'] == product_id), None)
            if found_item:
                found_item['quantity'] += 1
            else:
                image_path = product.get('image', '')
                cart.append({
                    'id': product_id,
                    'name': product['name'],
                    'price': product['price'],
                    'image': image_path,
                    'quantity': 1
                })
            session['cart'] = cart
            return jsonify(success=True)
        else:
            return jsonify(success=False, message=f'Product with ID {product_id} not found!')

    return redirect(url_for('home'))

@app.route('/remove_from_cart', methods=['POST'])
def remove_from_cart():
    item_id = request.json['item_id']
    cart = session.get('cart', [])
    session['cart'] = [item for item in cart if item.get('id') != item_id]
    return jsonify(success=True)

@app.route('/get_cart')
def get_cart():
    return jsonify(session.get('cart', []))

@app.route('/cart')
def cart():
    cart_items = session.get('cart', [])
    return render_template('cart.html', cart_items=cart_items)

@app.route('/index', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        keyword = request.form.get('keyword', '').lower()
        results = []
        with shelve.open(DATABASE) as db:
            for item_id, item in db.items():
                if keyword in item_id.lower() or keyword in item['name'].lower():
                    results.append({'id': item_id, **item})
        return render_template('search_results.html', results=results, keyword=keyword)
    return render_template('index.html')

@app.route('/add_product', methods=['GET', 'POST'])
def add_product():
    if request.method == 'POST':
        product_id = request.form['product_id']
        name = request.form['name']
        price = float(request.form['price'])
        stock = int(request.form['stock'])
        description = request.form['description']
        image = request.files.get('image')
        image_filename = None
        if image:
            image_filename = f"images/{product_id}_{image.filename}"
            image.save(f'./static/{image_filename}')
        with shelve.open(DATABASE, writeback=True) as db:
            if product_id in db:
                flash(f"Product ID '{product_id}' already exists!", 'error')
                return redirect(url_for('add_product'))
            db[product_id] = {
                'name': name,
                'price': price,
                'stock': stock,
                'description': description,
                'image': image_filename
            }
            flash(f"Product '{name}' added successfully!", 'success')
            return redirect(url_for('index'))
    return render_template('add_product.html')

@app.route('/edit/<item_id>', methods=['GET', 'POST'])
def edit_stock(item_id):
    with shelve.open(DATABASE, writeback=True) as db:
        if item_id not in db:
            flash('Item not found!', 'error')
            return redirect(url_for('index'))
        item = db[item_id]
        if request.method == 'POST':
            item['name'] = request.form['name']
            item['price'] = float(request.form['price'])
            item['stock'] = int(request.form['stock'])
            item['description'] = request.form['description']
            image = request.files.get('image')
            if image:
                image_filename = f"images/{item_id}_{image.filename}"
                image.save(f'./static/{image_filename}')
                item['image'] = image_filename
            db[item_id] = item
            flash('Stock updated successfully!', 'success')
            return redirect(url_for('index'))
        return render_template('edit_stock.html', item_id=item_id, item=item)

@app.route('/delete_stock/<string:item_id>', methods=['GET', 'POST'])
def delete_stock(item_id):
    with shelve.open(DATABASE) as db:
        if item_id in db:
            del db[item_id]
            flash(f"Item with ID {item_id} has been deleted successfully!", "success")
        else:
            flash(f"Item with ID {item_id} not found!", "danger")
    return redirect(url_for('index'))

@app.route('/all_products')
def all_products():
    with shelve.open(DATABASE) as db:
        products = []
        for product_id, item in db.items():
            products.append({'id': product_id, **item})
    return render_template('all_products.html', products=products)

@app.route('/populate')
def populate():
    with shelve.open(DATABASE) as db:
        db['CP001'] = {
            'name': 'CPU Intel i5',
            'price': 200.0,
            'stock': 50,
            'image': 'images/cpu_intel_i5.jpg',
            'description': 'Intel i5 processor'
        }
        db['CP002'] = {
            'name': 'GPU NVIDIA GTX 1660',
            'price': 400.0,
            'stock': 30,
            'image': 'images/gpu_nvidia_gtx_1660.jpg',
            'description': 'NVIDIA GTX 1660 graphics card'
        }
        db['CP003'] = {
            'name': 'RAM 16GB DDR4',
            'price': 80.0,
            'stock': 100,
            'image': 'images/ram_16gb_ddr4.jpg',
            'description': '16GB DDR4 RAM'
        }
        db['CP004'] = {
            'name': 'Motherboard ASUS Prime',
            'price': 150.0,
            'stock': 25,
            'image': 'motherboard_asus_prime.jpg',
            'description': 'ASUS Prime motherboard'
        }
        db['CP005'] = {
            'name': 'GeForce RTX 4070 Super',
            'price': 499.90,
            'stock': 50,
            'image': 'images/rtx-4070.jpg',
            'description': 'GeForce RTX 4070 Super graphics card'
        }
        db['CP006'] = {
            'name': 'G.Skill Trident Z5 Neo RGB (2x16GB DDR5-6000)',
            'price': 189.00,
            'stock': 30,
            'image': 'images/gskill-ram.jpg',
            'description': 'G.Skill Trident Z5 Neo RGB RAM'
        }
        db['CP007'] = {
            'name': 'AMD Ryzen 7 9700X',
            'price': 299.00,
            'stock': 100,
            'image': 'images/amd-ryzen.jpg',
            'description': 'AMD Ryzen 7 9700X processor'
        }
        db['PB001'] = {
            'name': 'The Average',
            'price': 715.0,
            'stock': 10,  
            'image': 'images/average_pc.jpg',
            'description': 'Ryzen 5 5600 + GeForce RTX 3050',
            'components': [
                "AMD Ryzen 5 5600 Processor",
                "AMD Wraith Stealth Cooler",
                "Gigabyte B550M DS3H AC Rev1.7",
                "Zotac RTX 3050 Solo - 6GB",
                "16GB Lexar Ares RGB DDR4 3600MHz (8x2)",
                "1TB Klevv C910 Gen4 SSD",
                "550W Gigabyte 80+ Silver (ATX3.0)"
            ]
        }

        db['PB002'] = {
            'name': 'The Monster',
            'price': 2015.0,
            'stock': 5,  
            'image': 'images/monster_pc.jpg',
            'description': 'Ryzen 7 7800X3D + GeForce RTX 4070 SUPER',
            'components': [
                "AMD Ryzen 7 7800X3D Processor",
                "Deepcool AK400 DIGITAL",
                "Gigabyte B650M Gaming Wifi",
                "Gigabyte RTX 4070 Super Windforce OC - 12GB",
                "32GB Lexar Thor RGB DDR5 6000MHz CL38 (16x2)",
                "1TB Klevv C910 Gen4 SSD",
                "850W Thermaltight 80+ Gold"
            ]
        }
    flash('Database populated!', 'success')
    return redirect(url_for('index'))

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

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/createTradeIn', methods=['GET','POST'])
def create_tradein():
    create_tradeIn_form = CreateTradeInForm(request.form)
    if request.method == 'POST' and create_tradeIn_form.validate():
        users_dict = {}
        db = shelve.open('user.db','c')
        try:
            users_dict = db['Users']
        except:
            print("Error In Retrieving Users From user.db")
        user = tradein.tradein(
            create_tradeIn_form.computer_component.data,
            create_tradeIn_form.part_types.data,
            create_tradeIn_form.condition.data,
            create_tradeIn_form.remarks.data
        )
        users_dict[user.get_trade_in()] = user
        db['Users'] = users_dict
        db.close()
        return redirect(url_for('details'))
    return render_template('createTradeIn.html', form=create_tradeIn_form)

@app.route('/retrieveTradeIn')
def retrieve_TradeIn():
    users_dict = {}
    db = shelve.open('user.db','r')
    users_dict = db['Users']
    db.close()
    users_list = []
    for key in users_dict:
        user = users_dict.get(key)
        users_list.append(user)
    return render_template('retrieveTradeIn.html', count=len(users_list), users_list=users_list)

@app.route('/updateUser/<int:id>/', methods=['GET','POST'])
def update_user(id):
    update_user_form = CreateTradeInForm(request.form)
    if request.method =='POST' and update_user_form.validate():
        users_dict = {}
        db = shelve.open('user.db','w')
        users_dict = db['Users']
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
        return render_template('updateUser.html', form=update_user_form)

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

@app.route('/admin')
def admin():
    if 'admin_logged_in' not in session:
        flash('Unauthorized access. Please log in as an admin.', 'error')
        return redirect(url_for('admin_login'))
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
        if admin_email == 'admin@example.com' and admin_password == 'admin':
            session['admin_logged_in'] = True
            session['admin_email'] = admin_email
            flash('Admin logged in successfully!', 'success')
            return redirect(url_for('admin'))
        else:
            flash('Invalid admin credentials.', 'error')
    return render_template('admin_login.html')

@app.route('/findus')
def findus():
    return render_template('findus.html')

@app.route('/admin_logout')
def admin_logout():
    session.clear()  
    return jsonify(success=True)  


@app.route('/logout')
def logout():
    session.clear()  
    return jsonify(success=True)  


@app.context_processor
def inject_user():
    return dict(user_email=session.get('email'))

if __name__ == '__main__':
    app.run(debug=True)