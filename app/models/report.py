from datetime import datetime
from app import db

class Report(db.Model):
    __tablename__ = 'reports'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    report_type = db.Column(db.String(50), nullable=False)  # activity, event, progress, issue
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    submitted_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    activity_id = db.Column(db.Integer, db.ForeignKey('activities.id'), nullable=True)  # Optional related activity
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    status = db.Column(db.String(20), default='submitted')  # submitted, reviewed, approved, rejected
    reviewed_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # Admin who reviewed
    reviewed_at = db.Column(db.DateTime, nullable=True)
    feedback = db.Column(db.Text, nullable=True)  # Admin feedback
    
    # Relationships
    school = db.relationship('School')
    submitter = db.relationship('User', foreign_keys=[submitted_by], backref='submitted_reports')
    reviewer = db.relationship('User', foreign_keys=[reviewed_by], backref='reviewed_reports')
    activity = db.relationship('Activity')
    attachments = db.relationship('ReportAttachment', backref='report', lazy='dynamic', cascade='all, delete-orphan')
    metrics = db.relationship('ReportMetric', backref='report', lazy='dynamic', cascade='all, delete-orphan')
    
    def __init__(self, title, report_type, school_id, submitted_by, description=None, activity_id=None):
        self.title = title
        self.report_type = report_type
        self.school_id = school_id
        self.submitted_by = submitted_by
        self.description = description
        self.activity_id = activity_id
    
    def review(self, admin_id, status, feedback=None):
        self.status = status
        self.reviewed_by = admin_id
        self.reviewed_at = datetime.utcnow()
        self.feedback = feedback
        db.session.commit()
    
    def add_attachment(self, file_path, file_type, description=None):
        attachment = ReportAttachment(report_id=self.id, file_path=file_path, 
                                     file_type=file_type, description=description)
        db.session.add(attachment)
        db.session.commit()
        return attachment
    
    def add_metric(self, name, value, unit=None):
        metric = ReportMetric(report_id=self.id, name=name, value=value, unit=unit)
        db.session.add(metric)
        db.session.commit()
        return metric
    
    def get_attachment_count(self):
        return self.attachments.count()
    
    def __repr__(self):
        return f'<Report {self.id}: {self.title} ({self.report_type})>'

class ReportAttachment(db.Model):
    __tablename__ = 'report_attachments'
    
    id = db.Column(db.Integer, primary_key=True)
    report_id = db.Column(db.Integer, db.ForeignKey('reports.id'), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)  # Path to the file
    file_type = db.Column(db.String(20), nullable=False)  # image, document, video, etc.
    description = db.Column(db.String(255), nullable=True)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __init__(self, report_id, file_path, file_type, description=None):
        self.report_id = report_id
        self.file_path = file_path
        self.file_type = file_type
        self.description = description
    
    def __repr__(self):
        return f'<Attachment {self.id} for Report {self.report_id}>'

class ReportMetric(db.Model):
    __tablename__ = 'report_metrics'
    
    id = db.Column(db.Integer, primary_key=True)
    report_id = db.Column(db.Integer, db.ForeignKey('reports.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)  # e.g., 'student_attendance', 'volunteer_count'
    value = db.Column(db.String(100), nullable=False)  # Stored as string to allow various formats
    unit = db.Column(db.String(20), nullable=True)  # e.g., 'people', '%', 'hours'
    
    def __init__(self, report_id, name, value, unit=None):
        self.report_id = report_id
        self.name = name
        self.value = value
        self.unit = unit
    
    def __repr__(self):
        return f'<Metric {self.name}: {self.value} {self.unit or ""} for Report {self.report_id}>'

class PerformanceReport(db.Model):
    __tablename__ = 'performance_reports'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    report_period = db.Column(db.String(50), nullable=False)  # monthly, quarterly, yearly
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=True)  # Optional, for school-specific reports
    generated_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    pdf_path = db.Column(db.String(255), nullable=True)  # Path to generated PDF
    is_public = db.Column(db.Boolean, default=False)  # Whether visible to all users
    
    # Relationships
    school = db.relationship('School', backref='performance_reports')
    generator = db.relationship('User', backref='generated_reports')
    sections = db.relationship('ReportSection', backref='performance_report', lazy='dynamic', cascade='all, delete-orphan')
    
    def __init__(self, title, report_period, start_date, end_date, generated_by, 
                 school_id=None, is_public=False):
        self.title = title
        self.report_period = report_period
        self.start_date = start_date
        self.end_date = end_date
        self.generated_by = generated_by
        self.school_id = school_id
        self.is_public = is_public
    
    def add_section(self, title, content, order=None):
        # If order not specified, add to end
        if order is None:
            max_order = db.session.query(db.func.max(ReportSection.order)).\
                filter(ReportSection.performance_report_id == self.id).scalar() or 0
            order = max_order + 1
        
        section = ReportSection(performance_report_id=self.id, title=title, content=content, order=order)
        db.session.add(section)
        db.session.commit()
        return section
    
    def generate_pdf(self, pdf_path):
        self.pdf_path = pdf_path
        db.session.commit()
    
    def __repr__(self):
        return f'<PerformanceReport {self.id}: {self.title} ({self.report_period})>'

class ReportSection(db.Model):
    __tablename__ = 'report_sections'
    
    id = db.Column(db.Integer, primary_key=True)
    performance_report_id = db.Column(db.Integer, db.ForeignKey('performance_reports.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)  # Can contain HTML for formatting
    order = db.Column(db.Integer, default=0)  # Order in the report
    
    def __init__(self, performance_report_id, title, content, order=0):
        self.performance_report_id = performance_report_id
        self.title = title
        self.content = content
        self.order = order
    
    def __repr__(self):
        return f'<ReportSection {self.id}: {self.title} for Report {self.performance_report_id}>'