from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from createTradeIn import CreateTradeInForm
import shelve, tradein, User, Customer
from SignupForm import SignUpForm
from Form import Login
from Forms import CreateUserForm, CreateCustomerForm
from User import User
from Form import AdminSignUpForm
from wtforms import Form, StringField, PasswordField, validators
import random
import string

app = Flask(__name__)
app.secret_key = 'supersecretkey'

DATABASE = 'inventory.db'

@app.before_request
def initialize_cart():
    if 'cart' not in session:
        session['cart'] = []



@app.route('/prebuilds')
def prebuilds():
    emoji_mapping = {
        "Processor": "🖥", "CPU": "🖥",
        "Cooler": "❄️",
        "Motherboard": "🛠",
        "GPU": "🎮", "Graphics Card": "🎮",
        "RAM": "🧠", "Memory": "🧠",
        "SSD": "💾", "HDD": "💾", "Storage": "💾",
        "Power Supply": "⚡", "PSU": "⚡"
    }

    prebuilts = []
    with shelve.open(DATABASE) as db:
        for product_id, item in db.items():
            if product_id.startswith('PB'):
                item['id'] = product_id

                new_components = []
                for comp in item.get('components', []):
                    if isinstance(comp, dict) and "tags" in comp and "name" in comp:
                        assigned_emoji = "💻"  

                        for tag in comp["tags"]:
                            if tag in emoji_mapping:
                                assigned_emoji = emoji_mapping[tag]
                                break

                        new_components.append(f"{assigned_emoji} {comp['name']}") 

                    else:
                        new_components.append(f"💻 {comp}")  

                item['components'] = new_components  
                prebuilts.append(item)

    return render_template('prebuild.html', prebuilts=prebuilts)





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

@app.route('/submit_review', methods=['POST'])
def submit_review():
    data = request.get_json()
    product_id = data.get('product_id')
    rating = int(data.get('rating', 0))
    comment = data.get('comment', '')

    if not product_id or rating < 1 or rating > 5:
        return jsonify(success=False, message="Invalid input")

    username = session.get('username')  

    with shelve.open(DATABASE, writeback=True) as db:
        if product_id not in db:
            return jsonify(success=False, message="Product not found")

        product = db[product_id]
        if 'reviews' not in product:
            product['reviews'] = []

        
        review_data = {'rating': rating, 'comment': comment}
        if username:
            review_data['username'] = username
        
        product['reviews'].append(review_data)

        total_ratings = sum(r['rating'] for r in product['reviews'])
        product['average_rating'] = round(total_ratings / len(product['reviews']), 1)

        db[product_id] = product

    return jsonify(success=True, average_rating=product['average_rating'], reviews=product['reviews'])


@app.route('/preview/<product_id>')
def preview(product_id):
    emoji_mapping = {
        "Processor": "🖥", "CPU": "🖥",
        "Cooler": "❄️",
        "Motherboard": "🛠",
        "GPU": "🎮", "Graphics Card": "🎮",
        "RAM": "🧠", "Memory": "🧠",
        "SSD": "💾", "HDD": "💾", "Storage": "💾",
        "Power Supply": "⚡", "PSU": "⚡"
    }

    with shelve.open(DATABASE) as db:
        if product_id in db:
            product = db[product_id]
            product['reviews'] = product.get('reviews', [])
            product['average_rating'] = product.get('average_rating', 0)

            
            new_components = []
            for comp in product.get('components', []):
                if isinstance(comp, dict) and "tags" in comp and "name" in comp:
                    assigned_emoji = "💻"  
                    for tag in comp["tags"]:
                        if tag in emoji_mapping:
                            assigned_emoji = emoji_mapping[tag]
                            break  
                    new_components.append(f"{assigned_emoji} {comp['name']}")  
                else:
                    new_components.append(f"💻 {comp}")  

            product['components'] = new_components 

            return render_template('preview.html', product=product, product_id=product_id)

        else:
            flash('Product not found!', 'error')
            return redirect(url_for('index'))

        
        
@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    data = request.get_json()
    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)

    with shelve.open(DATABASE) as db:
        if product_id in db:
            product = db[product_id]
            cart = session.get('cart', [])
            found_item = next((i for i in cart if i['id'] == product_id), None)
            if found_item:
                found_item['quantity'] += quantity
            else:
                image_path = product.get('image', '')
                cart.append({
                    'id': product_id,
                    'name': product['name'],
                    'price': product['price'],
                    'image': image_path,
                    'quantity': quantity
                })
            session['cart'] = cart
            return jsonify(success=True)
        else:
            return jsonify(success=False, message=f'Product with ID {product_id} not found!')

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
    with shelve.open(DATABASE, writeback=True) as db:
        db['CP001'] = {
            'id': 'CP001',
            'name': 'CPU Intel i5',
            'price': 200.0,
            'old_price': 234.0,
            'discount': 14,
            'stock': 50,
            'image': 'images/cpu_intel_i5.jpg',
            'description': 'The Intel Core i5 is a versatile mid-range processor offering strong multi-core performance.',
            'tags': ["Processor", "CPU"]
        }
        db['CP002'] = {
            'id': 'CP002',
            'name': 'GPU NVIDIA GTX 1660',
            'price': 400.0,
            'old_price': 460.0,
            'discount': 21,
            'stock': 30,
            'image': 'images/gpu_nvidia_gtx_1660.jpg',
            'description': 'The Nvidia GTX 1660 is a budget-friendly yet powerful GPU for 1080p gaming.',
            'tags': ["GPU", "Graphics Card"]
        }
        db['CP003'] = {
            'id': 'CP003',
            'name': 'RAM 16GB DDR4',
            'price': 68.80,
            'old_price': 80.0,
            'discount': 14,
            'stock': 100,
            'image': 'images/ram_16gb_ddr4.jpg',
            'description': 'Upgrade your PC with 16GB of DDR4 RAM for faster performance in gaming and content creation.',
            'tags': ["RAM", "Memory"]
        }
        db['CP004'] = {
            'id': 'CP004',
            'name': 'Motherboard ASUS Prime',
            'price': 150.0,
            'stock': 25,
            'image': 'images/motherboard_asus_prime.jpg',
            'description': 'The ASUS Prime motherboard provides a solid foundation for gaming and productivity.',
            'tags': ["Motherboard"]
        }
        db['CP005'] = {
            'id': 'CP005',
            'name': 'GeForce RTX 4070 Super',
            'price': 499.90,
            'old_price': 600.0,
            'discount': 17,
            'stock': 50,
            'image': 'images/rtx-4070.jpg',
            'description': 'The RTX 4070 Super delivers ultra-smooth gaming with ray tracing and AI-enhanced graphics.',
            'tags': ["GPU", "Graphics Card"]
        }
        db['CP006'] = {
            'id': 'CP006',
            'name': 'G.Skill Trident Z5 Neo RGB',
            'price': 189.00,
            'old_price': 230.00,
            'discount': 21,
            'stock': 30,
            'image': 'images/gskill-ram.jpg',
            'description': 'High-speed DDR5 RAM with stunning RGB lighting, ideal for gaming and overclocking.',
            'tags': ["RAM", "Memory"]
        }
        db['CP007'] = {
            'id': 'CP007',
            'name': 'AMD Ryzen 7 9700X',
            'price': 299.00,
            'old_price': 349.00,
            'discount': 15,
            'stock': 100,
            'image': 'images/amd-ryzen.jpg',
            'description': 'A high-performance processor with 8 cores and 16 threads for gaming and content creation.',
            'tags': ["Processor", "CPU"]
        }

        db['PB001'] = {
            'id': 'PB001',
            'name': 'The Average',
            'price': 715.0,
            'stock': 10,
            'image': 'images/average_pc.jpg',
            'description': 'A balanced gaming PC with Ryzen 5 5600 and RTX 3050.',
            'components': [
                {"name": "AMD Ryzen 5 5600 Processor", "tags": ["Processor", "CPU"]},
                {"name": "AMD Wraith Stealth Cooler", "tags": ["Cooler"]},
                {"name": "Gigabyte B550M DS3H AC Rev1.7", "tags": ["Motherboard"]},
                {"name": "Zotac RTX 3050 Solo - 6GB", "tags": ["GPU", "Graphics Card"]},
                {"name": "16GB Lexar Ares RGB DDR4 3600MHz (8x2)", "tags": ["RAM", "Memory"]},
                {"name": "1TB Klevv C910 Gen4 SSD", "tags": ["SSD", "Storage"]},
                {"name": "550W Gigabyte 80+ Silver (ATX3.0)", "tags": ["Power Supply", "PSU"]}
            ]
        }
        db['PB002'] = {
            'id': 'PB002',
            'name': 'The Monster',
            'price': 2015.0,
            'stock': 5,
            'image': 'images/monster_pc.jpg',
            'description': 'A high-end gaming PC with Ryzen 7 7800X3D and RTX 4070 SUPER.',
            'components': [
                {"name": "AMD Ryzen 7 7800X3D Processor", "tags": ["Processor", "CPU"]},
                {"name": "Deepcool AK400 DIGITAL", "tags": ["Cooler"]},
                {"name": "Gigabyte B650M Gaming Wifi", "tags": ["Motherboard"]},
                {"name": "Gigabyte RTX 4070 Super Windforce OC - 12GB", "tags": ["GPU", "Graphics Card"]},
                {"name": "32GB Lexar Thor RGB DDR5 6000MHz CL38 (16x2)", "tags": ["RAM", "Memory"]},
                {"name": "1TB Klevv C910 Gen4 SSD", "tags": ["SSD", "Storage"]},
                {"name": "850W Thermaltight 80+ Gold", "tags": ["Power Supply", "PSU"]}
            ]
        }

    return redirect(url_for('index'))



@app.route('/details')
def details():
    users_dict = {}
    discount_codes = []  # This list will store all generated codes
    try:
        db = shelve.open('user.db', 'r')
        users_dict = db['Users']
        db.close()
    except Exception as e:
        print(f"Error reading from database: {e}")

    users_list = []
    for key in users_dict:
        user = users_dict.get(key)
        component = user.get_types_component()
        condition = user.get_condition()
        code, value = generate_discount_code(component, condition, discount_codes)
        user.discount = value
        user.discount_code = code
        users_list.append(user)

    print(f"All generated discount codes and their values: {discount_codes}")  # Final print of all codes
    return render_template('details.html', users_list=users_list)


@app.route('/')
def home():
    products = []
    with shelve.open(DATABASE) as db:
        for product_id, item in db.items():
            if not product_id.startswith('PB'):  
                item['id'] = product_id  
                products.append(item)

    return render_template('home.html', products=products)

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

def generate_discount_code(component, condition, discount_codes=[]):
    characters = string.ascii_uppercase + string.digits
    code = ''.join(random.choices(characters, k=8))
    discount_value = discount(component, condition)
    discount_codes.append((code, discount_value))
    print(f"Generated code: {code}, Value: {discount_value}")  # Debug print
    print(f"Current list of discount codes: {discount_codes}")  # Debug print
    return code, discount_value

def discount(component, condition):
    discounts = {
        ('3060', 'Broken'): 50,
        ('3060', 'Well-Used'): 75,
        ('3060', 'Barely-Used'): 85,
        ('3060', 'Perfect'): 100,
        ('3060ti', 'Broken'): 50,
        ('3060ti', 'Well-Used'): 80,
        ('3060ti', 'Barely-Used'): 90,
        ('3060ti', 'Perfect'): 100,
        ('3070', 'Broken'): 50,
        ('3070', 'Well-Used'): 85,
        ('3070', 'Barely-Used'): 100,
        ('3070', 'Perfect'): 150,
        ('3070ti', 'Broken'): 50,
        ('3070ti', 'Well-Used'): 90,
        ('3070ti', 'Barely-Used'): 105,
        ('3070ti', 'Perfect'): 155,
        ('3080', 'Broken'): 50,
        ('3080', 'Well-Used'): 100,
        ('3080', 'Barely-Used'): 200,
        ('3080', 'Perfect'): 250,
        ('3080ti', 'Broken'): 50,
        ('3080ti', 'Well-Used'): 105,
        ('3080ti', 'Barely-Used'): 205,
        ('3080ti', 'Perfect'): 255,
        ('3090', 'Broken'): 50,
        ('3090', 'Well-Used'): 200,
        ('3090', 'Barely-Used'): 300,
        ('3090', 'Perfect'): 1000,
        ('3090ti', 'Broken'): 50,
        ('3090ti', 'Well-Used'): 210,
        ('3090ti', 'Barely-Used'): 310,
        ('3090ti', 'Perfect'): 1010,
        ('4060', 'Broken'): 50,
        ('4060', 'Well-Used'): 80,
        ('4060', 'Barely-Used'): 90,
        ('4060', 'Perfect'): 105,
        ('4060ti', 'Broken'): 50,
        ('4060ti', 'Well-Used'): 85,
        ('4060ti', 'Barely-Used'): 95,
        ('4060ti', 'Perfect'): 110,
        ('4070', 'Broken'): 50,
        ('4070', 'Well-Used'): 90,
        ('4070', 'Barely-Used'): 105,
        ('4070', 'Perfect'): 160,
        ('4070ti', 'Broken'): 50,
        ('4070ti', 'Well-Used'): 100,
        ('4070ti', 'Barely-Used'): 110,
        ('4070ti', 'Perfect'): 170,
        ('4080', 'Broken'): 50,
        ('4080', 'Well-Used'): 110,
        ('4080', 'Barely-Used'): 210,
        ('4080', 'Perfect'): 260,
        ('4080ti', 'Broken'): 50,
        ('4080ti', 'Well-Used'): 115,
        ('4080ti', 'Barely-Used'): 215,
        ('4080ti', 'Perfect'): 270,
        ('4090', 'Broken'): 50,
        ('4090', 'Well-Used'): 210,
        ('4090', 'Barely-Used'): 310,
        ('4090', 'Perfect'): 1020,
        ('4090ti', 'Broken'): 50,
        ('4090ti', 'Well-Used'): 220,
        ('4090ti', 'Barely-Used'): 320,
        ('4090ti', 'Perfect'): 1030,
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
    return discounts.get((component, condition), "No discount found")
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

@app.route('/contactUs')
def contact_us():
    return render_template('contactUs.html')
@app.route('/customerForum')
def customerForum():
    return render_template('customerForum.html')

@app.route('/adminForum')
def adminForum():
    return render_template('adminForum.html')


@app.route('/signup_cus', methods=['GET', 'POST'])
def signup_cus():
    form = SignUpForm(request.form)
    if request.method == 'POST':
        username = form.username.data
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
                db[email] = {'username': username, 'email': email, 'password': password}
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
                    session['username'] = db[email]['username']  
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
            users.append({
                'username': details.get('username', 'N/A'),  
                'email': email,
                'password': details['password']
            })
    
    return render_template('admin.html', users=users)

@app.route('/update_username', methods=['POST'])
def update_username():
    if 'admin_logged_in' not in session:
        return jsonify(success=False, message="Unauthorized access.")

    data = request.get_json()
    old_email = data.get('old_email')
    new_email = data.get('email')
    new_password = data.get('password')
    new_username = data.get('username')

    with shelve.open('users_db', writeback=True) as db:
        if old_email not in db:
            return jsonify(success=False, message="User not found.")
        
        # Update user details
        db[new_email] = {'username': new_username, 'email': new_email, 'password': new_password}

        # Remove the old email entry if changed
        if new_email != old_email:
            del db[old_email]
        
        db.sync()
    
    return jsonify(success=True)


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



@app.route('/admin_signup', methods=['GET', 'POST'])
def admin_signup():
    form = AdminSignUpForm(request.form)
    
    if request.method == 'POST' and form.validate():
        email = form.email.data
        password = form.password.data

        
        with shelve.open('admin_db', writeback=True) as db:
            
            if email in db:
                flash('Admin account already exists!', 'error')
                return redirect(url_for('admin_signup'))
            
            
            db[email] = {'email': email, 'password': password}
            flash("Admin account created successfully!", 'success')
            return redirect(url_for('admin_login'))  
    
    return render_template('admin_signup.html', form=form)


@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        admin_email = request.form.get('email')
        admin_password = request.form.get('password')

        
        with shelve.open('admin_db') as db:
            
            admin_data = db.get(admin_email, None)

            if admin_data:
                
                if admin_password == admin_data['password']:
                    session['admin_logged_in'] = True
                    session['admin_email'] = admin_email
                    flash('Admin logged in successfully!', 'success')
                    return redirect(url_for('admin'))  
                else:
                    flash('Invalid password. Please try again.', 'error')
            else:
                flash('Admin email not found. Please check your email or sign up.', 'error')

    return render_template('admin_login.html')


@app.route('/delete_review', methods=['POST'])
def delete_review():
    if 'admin_logged_in' not in session:
        return jsonify(success=False, message="Unauthorized access.")

    data = request.get_json()
    product_id = data.get('product_id')
    comment_index = int(data.get('comment_index', -1))

    with shelve.open(DATABASE, writeback=True) as db:
        if product_id not in db:
            return jsonify(success=False, message="Product not found.")

        product = db[product_id]

        if 'reviews' not in product or comment_index < 0 or comment_index >= len(product['reviews']):
            return jsonify(success=False, message="Invalid review index.")

        
        del product['reviews'][comment_index]

        
        if product['reviews']:
            total_ratings = sum(r['rating'] for r in product['reviews'])
            product['average_rating'] = round(total_ratings / len(product['reviews']), 1)
        else:
            product['average_rating'] = 0  

        db[product_id] = product
        return jsonify(success=True, average_rating=product['average_rating'], reviews=product['reviews'])

    
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

@app.context_processor
def inject_user():
    return dict(username=session.get('username'))

@app.context_processor
def inject_request():
    return dict(request=request)

if __name__ == '__main__':
    app.run(debug=True)