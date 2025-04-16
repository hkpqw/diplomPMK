from app import db, login
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(512))
    full_name = db.Column(db.String(128)) # Добавлено поле ФИО
    phone_number = db.Column(db.String(20)) # Добавлено поле номер телефона
    applications = db.relationship('Application', backref='author', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return '<User {}>'.format(self.username)

@login.user_loader
def load_user(id):
    return User.query.get(int(id))

class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), index=True)
    description = db.Column(db.Text)
    price = db.Column(db.Float)
    image_filename = db.Column(db.String(256))
    applications = db.relationship('Application', backref='service', lazy='dynamic')

    def __repr__(self):
        return '<Service {}>'.format(self.name)

class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'))
    status = db.Column(db.String(32), default='new')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return '<Application {}>'.format(self.name)

class News(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    content = db.Column(db.Text)
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    text = db.Column(db.Text)
    rating = db.Column(db.Integer)  # Например, от 1 до 5
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)