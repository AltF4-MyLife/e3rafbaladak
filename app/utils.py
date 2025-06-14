import os
import uuid
import secrets
from datetime import datetime
from PIL import Image
from flask import current_app, url_for
from flask_mail import Message
from werkzeug.utils import secure_filename
from app import mail

# File handling utilities
def allowed_file(filename, file_type):
    """Check if the file extension is allowed for the given file type."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS'].get(file_type, set())

def save_file(file, folder, file_type, max_size=(800, 800)):
    """Save a file to the specified folder with a secure filename.
    
    Args:
        file: The file object from the request
        folder: The subfolder within UPLOAD_FOLDER to save to
        file_type: Type of file ('image', 'document', 'video', 'audio')
        max_size: Maximum dimensions for image resizing (width, height)
        
    Returns:
        The filename of the saved file
    """
    if file and allowed_file(file.filename, file_type):
        # Generate a secure filename with a random component
        filename = secure_filename(file.filename)
        random_hex = secrets.token_hex(8)
        _, file_ext = os.path.splitext(filename)
        new_filename = random_hex + file_ext
        
        # Create the full path
        upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], folder)
        os.makedirs(upload_path, exist_ok=True)
        file_path = os.path.join(upload_path, new_filename)
        
        # Save the file
        if file_type == 'image':
            # Resize image if it's an image file
            img = Image.open(file)
            img.thumbnail(max_size)
            img.save(file_path)
        else:
            file.save(file_path)
            
        return new_filename
    return None

def save_image_with_thumbnail(file, folder, thumbnail_size=(200, 200)):
    """Save an image and create a thumbnail version.
    
    Args:
        file: The file object from the request
        folder: The subfolder within UPLOAD_FOLDER to save to
        thumbnail_size: Size for the thumbnail (width, height)
        
    Returns:
        A tuple of (main_filename, thumbnail_filename)
    """
    if file and allowed_file(file.filename, 'image'):
        # Generate a secure filename with a random component
        filename = secure_filename(file.filename)
        random_hex = secrets.token_hex(8)
        _, file_ext = os.path.splitext(filename)
        new_filename = random_hex + file_ext
        thumbnail_filename = random_hex + '_thumb' + file_ext
        
        # Create the full path
        upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], folder)
        os.makedirs(upload_path, exist_ok=True)
        file_path = os.path.join(upload_path, new_filename)
        thumbnail_path = os.path.join(upload_path, thumbnail_filename)
        
        # Save the main image (resized to a reasonable max size)
        img = Image.open(file)
        img.thumbnail((800, 800))  # Max size for main image
        img.save(file_path)
        
        # Create and save the thumbnail
        thumb = Image.open(file)
        thumb.thumbnail(thumbnail_size)
        thumb.save(thumbnail_path)
        
        return (new_filename, thumbnail_filename)
    return (None, None)

# Email utilities
def send_email(subject, recipients, template, **kwargs):
    """Send an email using a template.
    
    Args:
        subject: Email subject
        recipients: List of recipient email addresses
        template: The template to use for the email body
        **kwargs: Variables to pass to the template
    """
    msg = Message(subject, recipients=recipients)
    msg.html = template.format(**kwargs)
    mail.send(msg)

def send_volunteer_thank_you_email(volunteer):
    """Send a thank you email to a newly registered volunteer.
    
    Args:
        volunteer: The Volunteer model instance
    """
    with open(os.path.join(current_app.root_path, 'email_templates', 'thank_you.html'), 'r', encoding='utf-8') as f:
        template = f.read()
    
    send_email(
        'شكراً لانضمامك إلى مبادرة اعرف بلدك',
        [volunteer.email],
        template,
        name=volunteer.name,
        date=datetime.now().strftime('%Y-%m-%d')
    )

# PDF generation utilities
def generate_report_pdf(data, template_name):
    """Generate a PDF report using WeasyPrint.
    
    Args:
        data: The data to include in the report
        template_name: The name of the template to use
        
    Returns:
        The PDF as bytes
    """
    from weasyprint import HTML
    from flask import render_template
    
    html = render_template(f'reports/{template_name}.html', **data)
    return HTML(string=html).write_pdf()

# Data export utilities
def export_to_csv(data, fields):
    """Export data to CSV format.
    
    Args:
        data: List of data objects (e.g., database models)
        fields: List of field names to include
        
    Returns:
        CSV data as a string
    """
    import csv
    import io
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(fields)
    
    # Write data rows
    for item in data:
        row = [getattr(item, field) for field in fields]
        writer.writerow(row)
    
    return output.getvalue()

# String utilities
def generate_unique_slug(title, model, slug_field='slug'):
    """Generate a unique slug for a model based on a title.
    
    Args:
        title: The title to slugify
        model: The database model class
        slug_field: The name of the slug field in the model
        
    Returns:
        A unique slug string
    """
    from slugify import slugify
    from app import db
    
    slug = slugify(title, locale='ar')
    
    # Check if the slug already exists
    query = db.session.query(model).filter(getattr(model, slug_field) == slug)
    if query.count() > 0:
        # If it exists, append a random string
        slug = f"{slug}-{secrets.token_hex(4)}"
    
    return slug

# Security utilities
def generate_token():
    """Generate a secure random token for verification purposes."""
    return secrets.token_urlsafe(32)

# Date and time utilities
def format_datetime(value, format='%Y-%m-%d %H:%M'):
    """Format a datetime object to a string."""
    if value is None:
        return ""
    return value.strftime(format)

def get_current_year():
    """Get the current year for copyright notices."""
    return datetime.now().year

# RTL text handling
def is_rtl(text):
    """Check if text is primarily right-to-left."""
    # Simple check for Arabic characters
    arabic_count = sum(1 for c in text if 0x0600 <= ord(c) <= 0x06FF)
    return arabic_count > len(text) / 2


def send_password_reset_email(user):
    """Send a password reset email to a user.
    
    Args:
        user: The User model instance
    """
    token = user.get_reset_password_token()
    reset_url = url_for('auth.reset_password', token=token, _external=True)
    
    with open(os.path.join(current_app.root_path, 'email_templates', 'reset_password.html'), 'r', encoding='utf-8') as f:
        template = f.read()
    
    send_email(
        'إعادة تعيين كلمة المرور',
        [user.email],
        template,
        name=user.username,
        reset_url=reset_url
    )