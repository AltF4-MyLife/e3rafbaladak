from datetime import datetime
from app import db

class School(db.Model):
    __tablename__ = 'schools'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(200), nullable=False)  # City/Governorate
    address = db.Column(db.String(200), nullable=False)  # Detailed address
    student_count = db.Column(db.Integer, default=0)
    phone = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    logo = db.Column(db.String(100), nullable=True)  # Path to logo image
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    volunteers = db.relationship('Volunteer', backref='school', lazy='dynamic')
    reports = db.relationship('Report', lazy='dynamic')
    activities = db.relationship('Activity', backref='school', lazy='dynamic')
    
    def __init__(self, name, location, address, email, student_count=0, phone=None, logo=None):
        self.name = name
        self.location = location
        self.address = address
        self.email = email
        self.student_count = student_count
        self.phone = phone
        self.logo = logo
    
    def update(self, name=None, location=None, address=None, email=None, 
               student_count=None, phone=None, logo=None):
        if name:
            self.name = name
        if location:
            self.location = location
        if address:
            self.address = address
        if email:
            self.email = email
        if student_count is not None:
            self.student_count = student_count
        if phone:
            self.phone = phone
        if logo:
            self.logo = logo
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def get_volunteer_count(self):
        return self.volunteers.count()
    
    def get_activity_count(self):
        return self.activities.count()
    
    def get_report_count(self):
        return self.reports.count()
    
    def get_recent_activities(self, limit=5):
        return self.activities.order_by(Activity.date.desc()).limit(limit).all()
    
    def get_recent_reports(self, limit=5):
        return self.reports.order_by(Report.created_at.desc()).limit(limit).all()
    
    def __repr__(self):
        return f'<School {self.name}({self.location})>'

class Activity(db.Model):
    __tablename__ = 'activities'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    location = db.Column(db.String(200), nullable=True)  # Specific location within the school
    participants_count = db.Column(db.Integer, default=0)
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    status = db.Column(db.String(20), default='planned')  # planned, ongoing, completed, cancelled
    
    # Relationships
    media_items = db.relationship('Media', backref='activity', lazy='dynamic')
    reports = db.relationship('Report', lazy='dynamic')
    
    def __init__(self, title, description, date, school_id, location=None, 
                 participants_count=0, status='planned'):
        self.title = title
        self.description = description
        self.date = date
        self.school_id = school_id
        self.location = location
        self.participants_count = participants_count
        self.status = status
    
    def update_status(self, status):
        valid_statuses = ['planned', 'ongoing', 'completed', 'cancelled']
        if status in valid_statuses:
            self.status = status
            self.updated_at = datetime.utcnow()
            db.session.commit()
            return True
        return False
    
    def get_media_count(self):
        return self.media_items.count()
    
    def __repr__(self):
        return f'<Activity {self.title} ({self.date.strftime("%Y-%m-%d")})>'