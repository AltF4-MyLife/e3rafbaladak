from datetime import datetime
from flask import current_app
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from time import time
from app import db, login_manager

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), default='visitor')  # visitor, volunteer, school_coordinator, admin
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    profile_image = db.Column(db.String(100), nullable=True)
    
    # Relationships
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=True)
    school = db.relationship('School', backref=db.backref('coordinators', lazy=True))
    
    # For volunteers who are also users
    volunteer_id = db.Column(db.Integer, db.ForeignKey('volunteers.id'), nullable=True)
    volunteer = db.relationship('Volunteer', backref=db.backref('user_account', lazy=True, uselist=False))
    
    # User activity
    notifications = db.relationship('Notification', backref='user', lazy='dynamic')
    
    def __init__(self, name, email, role='visitor', school_id=None, volunteer_id=None):
        self.name = name
        self.email = email
        self.role = role
        self.school_id = school_id
        self.volunteer_id = volunteer_id
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_reset_password_token(self, expires_in=3600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            current_app.config['SECRET_KEY'],
            algorithm='HS256'
        )
    
    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(
                token,
                current_app.config['SECRET_KEY'],
                algorithms=['HS256']
            )['reset_password']
        except:
            return None
        return User.query.get(id)
    
    def is_admin(self):
        return self.role == 'admin'
    
    def is_school_coordinator(self):
        return self.role == 'school_coordinator'
    
    def is_volunteer(self):
        return self.role == 'volunteer'
    
    def update_last_login(self):
        self.last_login = datetime.utcnow()
        db.session.commit()
    
    def __repr__(self):
        return f'<User {self.name}({self.email})>'

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

class Notification(db.Model):
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    message = db.Column(db.String(250), nullable=False)
    category = db.Column(db.String(20), default='info')  # info, success, warning, danger
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    link = db.Column(db.String(250), nullable=True)  # Optional link to redirect when clicked
    
    def __init__(self, user_id, message, category='info', link=None):
        self.user_id = user_id
        self.message = message
        self.category = category
        self.link = link
    
    def mark_as_read(self):
        self.is_read = True
        db.session.commit()
    
    def __repr__(self):
        return f'<Notification {self.id}: {self.message[:20]}...>'