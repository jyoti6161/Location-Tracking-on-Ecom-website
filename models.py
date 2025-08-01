from extensions import db
from flask_login import UserMixin

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default="customer")  # customer/admin

class Restaurant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    rating = db.Column(db.Float, default=4.5)
    category = db.Column(db.String(100), default="Indian")
    image_url = db.Column(db.String(300), default="/static/images/restaurants/default.jpg")

    dishes = db.relationship("Dish", backref="restaurant", cascade="all, delete")

class Dish(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    price = db.Column(db.Float, nullable=False)
    image_url = db.Column(db.String(300), default="/static/images/dishes/default.jpg")
    restaurant_id = db.Column(db.Integer, db.ForeignKey("restaurant.id"))

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    restaurant_id = db.Column(db.Integer, db.ForeignKey("restaurant.id"))
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default="pending")
