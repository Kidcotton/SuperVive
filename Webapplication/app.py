from flask import Flask, render_template, request, redirect, url_for, flash
import shelve

app = Flask(__name__)
app.secret_key = 'supersecretkey'

DATABASE = 'inventory.db'


@app.route('/', methods=['GET', 'POST'])
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
            image.save(f'./static/{image_filename}')  # Save the image to the static folder

        with shelve.open(DATABASE, writeback=True) as db:
            if product_id in db:
                flash(f"Product ID '{product_id}' already exists!", 'error')
                return redirect(url_for('add_product'))

            db[product_id] = {
                'name': name, 
                'price': price, 
                'stock': stock,
                'description': description,
                'image': image_filename  # Store the image filename in the database
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
                item['image'] = image_filename  # Update the image filename in the database

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
        db['CP001'] = {'name': 'CPU Intel i5', 'price': 200.0, 'stock': 50, 
                       'image': 'cpu_intel_i5.jpg', 'description': 'Intel i5 processor'}
        db['CP002'] = {'name': 'GPU NVIDIA GTX 1660', 'price': 400.0, 'stock': 30,
                       'image': 'gpu_nvidia_gtx_1660.jpg', 'description': 'NVIDIA GTX 1660 graphics card'}
        db['CP003'] = {'name': 'RAM 16GB DDR4', 'price': 80.0, 'stock': 100,
                       'image': 'ram_16gb_ddr4.jpg', 'description': '16GB DDR4 RAM'}
        db['CP004'] = {'name': 'Motherboard ASUS Prime', 'price': 150.0, 'stock': 25,
                       'image': 'motherboard_asus_prime.jpg', 'description': 'ASUS Prime motherboard'}

    flash('Database populated!', 'success')
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
