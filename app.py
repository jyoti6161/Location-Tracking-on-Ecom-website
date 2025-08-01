from flask import Flask, render_template, jsonify, request
from config import Config
from extensions import db, bcrypt, login_manager
from models import User, Restaurant, Dish, Order

import os
import uuid
from flask import Flask, request, jsonify
import threading
from kafka_service.consumer_app  import start_consumer

from kafka_service.location_store import latest_location


UPLOAD_FOLDER = os.path.join("static", "images")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

# ✅ Ensure folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
      return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS



def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

    

    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # ✅ API routes
    register_routes(app)

    # ✅ Page routes
    @app.route("/")
    def home():
        return render_template("index.html")

    @app.route("/login")
    def login_page():
        return render_template("login.html")

    @app.route("/menu/<int:restaurant_id>")
    def menu_page(restaurant_id):
        return render_template("menu.html", restaurant_id=restaurant_id)

    @app.route("/myorders")
    def my_orders_page():
        return render_template("myorders.html")

    @app.route("/admin")
    def admin_panel():
        return render_template("admin_panel.html")

    return app

def register_routes(app):
    # ✅ Get all restaurants
    @app.route("/restaurants/", methods=["GET"])
    def get_restaurants():
        restaurants = Restaurant.query.all()
        return jsonify([
            {
                "id": r.id,
                "name": r.name,
                "location": r.location,
                "rating": r.rating,
                "category": r.category,
                "image_url": r.image_url
            } for r in restaurants
        ])

    # ✅ Get menu for a restaurant
    @app.route("/restaurants/<int:restaurant_id>/menu", methods=["GET"])
    def get_menu(restaurant_id):
        dishes = Dish.query.filter_by(restaurant_id=restaurant_id).all()
        return jsonify([
            {"id": d.id, "name": d.name, "price": d.price, "image_url": d.image_url}
            for d in dishes
        ])

    # ✅ Place order
    @app.route("/orders/place", methods=["POST"])
    def place_order():
        data = request.json
        user_id = data.get("user_id")
        restaurant_id = data.get("restaurant_id")
        total_amount = data.get("total_amount", 0.0)

        new_order = Order(
            user_id=user_id,
            restaurant_id=restaurant_id,
            total_amount=total_amount,
            status="pending"
        )
        db.session.add(new_order)
        db.session.commit()

        return jsonify({"message": "✅ Order placed successfully!", "order_id": new_order.id})

    # ✅ Get user's orders
    @app.route("/orders/myorders/<int:user_id>", methods=["GET"])
    def my_orders(user_id):
        orders = Order.query.filter_by(user_id=user_id).all()
        return jsonify([
            {
                "order_id": o.id,
                "restaurant": Restaurant.query.get(o.restaurant_id).name,
                "total_amount": o.total_amount,
                "status": o.status
            } for o in orders
        ])

    # ✅ Signup
    @app.route("/auth/signup", methods=["POST"])
    def signup():
        data = request.json
        name = data["name"]
        email = data["email"]
        password = bcrypt.generate_password_hash(data["password"]).decode("utf-8")
        role = data.get("role", "customer")

        if User.query.filter_by(email=email).first():
            return jsonify({"success": False, "message": "❌ Email already exists"})

        new_user = User(name=name, email=email, password=password, role=role)
        db.session.add(new_user)
        db.session.commit()

        return jsonify({"success": True, "message": "✅ Signup successful!"})

    # ✅ Login
    @app.route("/auth/login", methods=["POST"])
    def login():
        data = request.json
        email = data.get("email")
        password = data.get("password")

        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({"success": False, "message": "❌ User not found!"})

        if bcrypt.check_password_hash(user.password, password):
            return jsonify({
                "success": True,
                "message": "✅ Login successful!",
                "user_id": user.id,
                "role": user.role
            })
        else:
            return jsonify({"success": False, "message": "❌ Incorrect password"})


    @app.route("/admin/manage_menu/<int:restaurant_id>")
    def manage_menu_page(restaurant_id):
        return render_template("manage_menu.html", restaurant_id=restaurant_id)
    
    


    @app.route("/upload_image", methods=["POST"])
    def upload_image():
        if "image" not in request.files:
           return jsonify({"error": "No image file found"}), 400
    
        file = request.files["image"]
    
        if file.filename == "":
          return jsonify({"error": "No selected file"}), 400

        if file and allowed_file(file.filename):
        # ✅ Generate unique filename
           ext = file.filename.rsplit(".", 1)[1].lower()
           unique_filename = f"{uuid.uuid4().hex}.{ext}"
           save_path = os.path.join(app.config["UPLOAD_FOLDER"], unique_filename)
           file.save(save_path)
           return jsonify({"image_url": f"/static/images/{unique_filename}"})
    
        return jsonify({"error": "Invalid file format"}), 400



    @app.route("/location/latest")
    def get_latest_location():
         
        return jsonify(latest_location)


    
    @app.route('/track')
    def track_page():
        return render_template('track_location.html')



app = create_app()

if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    from kafka_service.consumer_app import start_consumer
    import threading

    consumer_thread = threading.Thread(target=start_consumer, daemon=True)
    consumer_thread.start()

    app.run(debug=True)
