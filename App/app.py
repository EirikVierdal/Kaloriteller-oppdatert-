from flask import Flask, request, render_template, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import requests
import os
from werkzeug.utils import secure_filename
from datetime import date
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.secret_key = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///products.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
HEADERS = {
    'User-Agent': 'FoodNutrientApp - Python - Version 1.0 - https://example.com'
}

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    weight = db.Column(db.Float, nullable=False)
    calories = db.Column(db.Float, nullable=False)
    proteins = db.Column(db.Float, nullable=False)
    fat = db.Column(db.Float, nullable=False)
    carbohydrates = db.Column(db.Float, nullable=False)
    image = db.Column(db.String(200), nullable=True)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def format_value(value):
    try:
        return f"{float(value):.1f}" if value is not None else "N/A"
    except ValueError:
        return "N/A"

def calculate_total_nutrient(per_100g_value, total_weight):
    try:
        if per_100g_value is None or total_weight is None:
            return "N/A"
        per_100g_value = float(per_100g_value)
        total_weight = float(total_weight)
        total_value = (per_100g_value * total_weight) / 100
        return f"{total_value:.1f}"
    except ValueError:
        return "N/A"

def search_products_in_norway(query, page_size=10):
    user_added_products = Product.query.filter(Product.name.contains(query)).all()
    custom_products = [
        {
            "name": product.name,
            "weight": product.weight,
            "calories_per_100g": format_value((product.calories / product.weight) * 100),
            "proteins_per_100g": format_value((product.proteins / product.weight) * 100),
            "fat_per_100g": format_value((product.fat / product.weight) * 100),
            "carbohydrates_per_100g": format_value((product.carbohydrates / product.weight) * 100),
            "total_calories": format_value(product.calories),
            "total_proteins": format_value(product.proteins),
            "total_fat": format_value(product.fat),
            "total_carbohydrates": format_value(product.carbohydrates),
            "image_url": product.image if product.image else "/static/default_image.png"
        }
        for product in user_added_products
    ]

    url = f"https://no.openfoodfacts.org/cgi/search.pl?action=process&tagtype_0=countries&tag_contains_0=contains&tag_0=norway&search_terms={query}&json=true&page_size={page_size}"
    response = requests.get(url, headers=HEADERS)
    
    if response.status_code == 200:
        data = response.json()
        products = data.get('products', [])
        api_products = [
            {
                "name": product.get("product_name", "N/A"),
                "weight": product.get("product_quantity", "N/A"),
                "calories_per_100g": format_value(product.get("nutriments", {}).get("energy-kcal_100g")),
                "proteins_per_100g": format_value(product.get("nutriments", {}).get("proteins_100g")),
                "fat_per_100g": format_value(product.get("nutriments", {}).get("fat_100g")),
                "carbohydrates_per_100g": format_value(product.get("nutriments", {}).get("carbohydrates_100g")),
                "total_calories": calculate_total_nutrient(product.get("nutriments", {}).get("energy-kcal_100g"), product.get("product_quantity")),
                "total_proteins": calculate_total_nutrient(product.get("nutriments", {}).get("proteins_100g"), product.get("product_quantity")),
                "total_fat": calculate_total_nutrient(product.get("nutriments", {}).get("fat_100g"), product.get("product_quantity")),
                "total_carbohydrates": calculate_total_nutrient(product.get("nutriments", {}).get("carbohydrates_100g"), product.get("product_quantity")),
                "image_url": product.get("image_url", "/static/default_image.png")
            }
            for product in products
        ]
        return custom_products + api_products
    return custom_products

@app.route('/')
@login_required
def index():
    products = Product.query.all()
    return render_template('index.html', saved_products=products, date=date.today(), current_user=current_user)

@app.route('/search', methods=['POST'])
@login_required
def search():
    query = request.form.get('search')
    products = search_products_in_norway(query)
    return render_template('sok_resultat.html', produkter=products)

@app.route('/add_product', methods=['POST'])
@login_required
def add_product():
    product_name = request.form.get('product_name')
    total_weight = float(request.form.get('weight'))
    proteins_per_100g = float(request.form.get('proteiner'))
    fat_per_100g = float(request.form.get('fett'))
    carbohydrates_per_100g = float(request.form.get('karbohydrater'))
    
    total_proteins = (proteins_per_100g * total_weight) / 100
    total_fat = (fat_per_100g * total_weight) / 100
    total_carbohydrates = (carbohydrates_per_100g * total_weight) / 100
    calories_per_100g = (proteins_per_100g * 4) + (carbohydrates_per_100g * 4) + (fat_per_100g * 9)
    total_calories = (calories_per_100g * total_weight) / 100
    
    file = request.files.get('product_image')
    image_path = None
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(image_path)

    new_product = Product(
        name=product_name,
        weight=total_weight,
        calories=total_calories,
        proteins=total_proteins,
        fat=total_fat,
        carbohydrates=total_carbohydrates,
        image=image_path
    )
    db.session.add(new_product)
    db.session.commit()
    flash('Product added successfully!')
    return redirect(url_for('index'))

@app.route('/delete_product/<int:product_id>', methods=['POST'])
@login_required
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    flash('Product deleted successfully!')
    return redirect(url_for('index'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

if __name__ == "__main__":
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    app.run(debug=True)
