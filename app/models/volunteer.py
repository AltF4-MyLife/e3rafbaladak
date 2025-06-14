from datetime import datetime
from app import db

class Volunteer(db.Model):
    __tablename__ = 'volunteers'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    skills = db.Column(db.String(50), nullable=False)  # Primary skill category
    other_skills = db.Column(db.String(200), nullable=True)  # Additional skills
    grade = db.Column(db.String(20), nullable=False)  # School grade/year
    registration_date = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    email_confirmed = db.Column(db.Boolean, default=False)
    confirmation_token = db.Column(db.String(100), nullable=True)
    
    # Relationships
    contributions = db.relationship('Contribution', backref='volunteer', lazy='dynamic')
    
    def __init__(self, name, email, school_id, skills, grade, phone=None, other_skills=None, availability=None, experience=None):
        self.name = name
        self.email = email
        self.school_id = school_id
        self.skills = skills
        self.grade = grade
        self.phone = phone
        self.other_skills = other_skills
        self.availability = availability
        self.experience = experience
    
    def confirm_email(self):
        self.email_confirmed = True
        self.confirmation_token = None
        db.session.commit()
    
    def deactivate(self):
        self.is_active = False
        db.session.commit()
    
    def reactivate(self):
        self.is_active = True
        db.session.commit()
    
    def update(self, name=None, email=None, phone=None, school_id=None, 
               skills=None, other_skills=None, grade=None):
        if name:
            self.name = name
        if email:
            self.email = email
        if phone:
            self.phone = phone
        if school_id:
            self.school_id = school_id
        if skills:
            self.skills = skills
        if other_skills:
            self.other_skills = other_skills
        if grade:
            self.grade = grade
        db.session.commit()
    
    def get_contribution_count(self):
        return self.contributions.count()
    
    def get_recent_contributions(self, limit=5):
        return self.contributions.order_by(Contribution.created_at.desc()).limit(limit).all()
    
    def __repr__(self):
        return f'<Volunteer {self.name}({self.email})>'

class Contribution(db.Model):
    __tablename__ = 'contributions'
    
    id = db.Column(db.Integer, primary_key=True)
    volunteer_id = db.Column(db.Integer, db.ForeignKey('volunteers.id'), nullable=False)
    contribution_type = db.Column(db.String(20), nullable=False)  # media, article, report, activity
    item_id = db.Column(db.Integer, nullable=False)  # ID of the contributed item
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text, nullable=True)
    
    def __init__(self, volunteer_id, contribution_type, item_id, notes=None):
        self.volunteer_id = volunteer_id
        self.contribution_type = contribution_type
        self.item_id = item_id
        self.notes = notes
    
    def get_item(self):
        """Get the actual contributed item based on contribution_type"""
        if self.contribution_type == 'media':
            from app.models.media import Media
            return Media.query.get(self.item_id)
        elif self.contribution_type == 'article':
            from app.models.article import Article
            return Article.query.get(self.item_id)
        elif self.contribution_type == 'report':
            from app.models.report import Report
            return Report.query.get(self.item_id)
        return None
    
    def __repr__(self):
        return f'<Contribution {self.id} by Volunteer {self.volunteer_id}>'