from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify
from flask_login import login_required, current_user
from app.models.user import User, Notification
from app.models.school import School
from app.models.volunteer import Volunteer
from app.models.article import Article
from app.models.media import Media
from app.models.report import Report, PerformanceReport
from app import db
from app.utils import generate_report_pdf, export_to_csv
from datetime import datetime, timedelta
import os
import json

admin = Blueprint('admin', __name__)

# Admin access decorator
def admin_required(f):
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@admin.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    """Admin dashboard"""
    # Get counts for dashboard
    user_count = User.query.count()
    school_count = School.query.count()
    volunteer_count = Volunteer.query.count()
    article_count = Article.query.count()
    media_count = Media.query.count()
    
    # Get recent users
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    
    # Get pending approvals
    pending_media = Media.query.filter_by(is_approved=False).count()
    pending_reports = Report.query.filter_by(status='submitted').count()
    
    # Get recent activity
    recent_logins = User.query.filter(User.last_login_at != None)\
        .order_by(User.last_login_at.desc()).limit(10).all()
    
    return render_template('admin/dashboard.html',
                           user_count=user_count,
                           school_count=school_count,
                           volunteer_count=volunteer_count,
                           article_count=article_count,
                           media_count=media_count,
                           recent_users=recent_users,
                           pending_media=pending_media,
                           pending_reports=pending_reports,
                           recent_logins=recent_logins)

@admin.route('/admin/users')
@login_required
@admin_required
def admin_users():
    """Manage users"""
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['PAGINATION_PER_PAGE']
    
    users = User.query.order_by(User.created_at.desc()).paginate(page=page, per_page=per_page)
    
    return render_template('admin/users.html', users=users)

@admin.route('/admin/users/<int:id>')
@login_required
@admin_required
def admin_user_detail(id):
    """View user details"""
    user = User.query.get_or_404(id)
    return render_template('admin/user_detail.html', user=user)

@admin.route('/admin/users/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_user_edit(id):
    """Edit user"""
    user = User.query.get_or_404(id)
    
    if request.method == 'POST':
        # Update user details
        user.username = request.form.get('username')
        user.email = request.form.get('email')
        user.role = request.form.get('role')
        user.is_active = 'is_active' in request.form
        
        # Update school_id if role is school_coordinator
        if user.role == 'school_coordinator':
            school_id = request.form.get('school_id', type=int)
            if school_id:
                user.school_id = school_id
        else:
            user.school_id = None
        
        db.session.commit()
        flash('User updated successfully!', 'success')
        return redirect(url_for('admin.admin_user_detail', id=user.id))
    
    # Get schools for dropdown if needed
    schools = School.query.order_by(School.name).all()
    
    return render_template('admin/user_edit.html', user=user, schools=schools)

@admin.route('/admin/users/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def admin_user_delete(id):
    """Delete user"""
    user = User.query.get_or_404(id)
    
    # Don't allow deleting yourself
    if user.id == current_user.id:
        flash('You cannot delete your own account.', 'danger')
        return redirect(url_for('admin.admin_users'))
    
    db.session.delete(user)
    db.session.commit()
    
    flash('User deleted successfully!', 'success')
    return redirect(url_for('admin.admin_users'))

@admin.route('/admin/schools')
@login_required
@admin_required
def admin_schools():
    """Manage schools"""
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['PAGINATION_PER_PAGE']
    
    schools = School.query.order_by(School.name).paginate(page=page, per_page=per_page)
    
    return render_template('admin/schools.html', schools=schools)

@admin.route('/admin/volunteers')
@login_required
@admin_required
def admin_volunteers():
    """Manage volunteers"""
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['PAGINATION_PER_PAGE']
    
    # Get filter parameters
    school_id = request.args.get('school_id', type=int)
    status = request.args.get('status')
    
    # Build query
    query = Volunteer.query
    
    if school_id:
        query = query.filter_by(school_id=school_id)
    
    if status:
        query = query.filter_by(status=status)
    
    volunteers = query.order_by(Volunteer.created_at.desc()).paginate(page=page, per_page=per_page)
    
    # Get schools for filter dropdown
    schools = School.query.order_by(School.name).all()
    
    return render_template('admin/volunteers.html', 
                           volunteers=volunteers, 
                           schools=schools,
                           current_school_id=school_id,
                           current_status=status)

@admin.route('/admin/articles')
@login_required
@admin_required
def admin_articles():
    """Manage articles"""
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['PAGINATION_PER_PAGE']
    
    # Get filter parameters
    category = request.args.get('category')
    is_published = request.args.get('is_published')
    
    # Build query
    query = Article.query
    
    if category:
        query = query.filter_by(category=category)
    
    if is_published is not None:
        query = query.filter_by(is_published=(is_published == 'true'))
    
    articles = query.order_by(Article.created_at.desc()).paginate(page=page, per_page=per_page)
    
    return render_template('admin/articles.html', 
                           articles=articles,
                           current_category=category,
                           current_is_published=is_published)

@admin.route('/admin/media')
@login_required
@admin_required
def admin_media():
    """Manage media"""
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['PAGINATION_PER_PAGE']
    
    # Get filter parameters
    media_type = request.args.get('media_type')
    is_approved = request.args.get('is_approved')
    
    # Build query
    query = Media.query
    
    if media_type:
        query = query.filter_by(media_type=media_type)
    
    if is_approved is not None:
        query = query.filter_by(is_approved=(is_approved == 'true'))
    
    media = query.order_by(Media.created_at.desc()).paginate(page=page, per_page=per_page)
    
    return render_template('admin/media.html', 
                           media=media,
                           current_media_type=media_type,
                           current_is_approved=is_approved)

@admin.route('/admin/reports')
@login_required
@admin_required
def admin_reports():
    """Manage reports"""
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['PAGINATION_PER_PAGE']
    
    # Get filter parameters
    report_type = request.args.get('report_type')
    status = request.args.get('status')
    
    # Build query
    query = Report.query
    
    if report_type:
        query = query.filter_by(report_type=report_type)
    
    if status:
        query = query.filter_by(status=status)
    
    reports = query.order_by(Report.created_at.desc()).paginate(page=page, per_page=per_page)
    
    return render_template('admin/reports.html', 
                           reports=reports,
                           current_report_type=report_type,
                           current_status=status)

@admin.route('/admin/reports/<int:id>/review', methods=['POST'])
@login_required
@admin_required
def admin_report_review(id):
    """Review a report"""
    report = Report.query.get_or_404(id)
    
    status = request.form.get('status')
    feedback = request.form.get('feedback')
    
    if status not in ['approved', 'rejected']:
        flash('Invalid status.', 'danger')
        return redirect(url_for('admin.admin_reports'))
    
    report.review(current_user.id, status, feedback)
    
    flash('Report reviewed successfully!', 'success')
    return redirect(url_for('admin.admin_reports'))

@admin.route('/admin/media/<int:id>/approve', methods=['POST'])
@login_required
@admin_required
def admin_media_approve(id):
    """Approve media"""
    media = Media.query.get_or_404(id)
    
    media.approve(current_user.id)
    
    flash('Media approved successfully!', 'success')
    return redirect(url_for('admin.admin_media'))

@admin.route('/admin/media/<int:id>/reject', methods=['POST'])
@login_required
@admin_required
def admin_media_reject(id):
    """Reject media"""
    media = Media.query.get_or_404(id)
    
    media.reject()
    
    flash('Media rejected.', 'success')
    return redirect(url_for('admin.admin_media'))

@admin.route('/admin/notifications')
@login_required
def admin_notifications():
    """View notifications"""
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['PAGINATION_PER_PAGE']
    
    notifications = Notification.query.filter_by(user_id=current_user.id)\
        .order_by(Notification.created_at.desc()).paginate(page=page, per_page=per_page)
    
    # Mark all as read
    for notification in notifications.items:
        if not notification.is_read:
            notification.is_read = True
    
    db.session.commit()
    
    return render_template('admin/notifications.html', notifications=notifications)

@admin.route('/admin/notifications/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_notification():
    """Create a notification for users"""
    if request.method == 'POST':
        title = request.form.get('title')
        message = request.form.get('message')
        category = request.form.get('category')
        recipient_role = request.form.get('recipient_role')
        
        if not title or not message or not category or not recipient_role:
            flash('All fields are required.', 'danger')
            return redirect(url_for('admin.create_notification'))
        
        # Get recipients based on role
        if recipient_role == 'all':
            recipients = User.query.all()
        else:
            recipients = User.query.filter_by(role=recipient_role).all()
        
        # Create notification for each recipient
        for user in recipients:
            notification = Notification(
                user_id=user.id,
                title=title,
                message=message,
                category=category
            )
            db.session.add(notification)
        
        db.session.commit()
        
        flash(f'Notification sent to {len(recipients)} users.', 'success')
        return redirect(url_for('admin.admin_dashboard'))
    
    return render_template('admin/create_notification.html')

@admin.route('/admin/stats')
@login_required
@admin_required
def admin_stats():
    """View platform statistics"""
    # User stats
    total_users = User.query.count()
    admin_users = User.query.filter_by(role='admin').count()
    school_coordinators = User.query.filter_by(role='school_coordinator').count()
    volunteers_registered = Volunteer.query.count()
    
    # Content stats
    total_articles = Article.query.count()
    published_articles = Article.query.filter_by(is_published=True).count()
    total_media = Media.query.count()
    approved_media = Media.query.filter_by(is_approved=True).count()
    
    # School stats
    total_schools = School.query.count()
    
    # Get user registration over time (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    user_registrations = db.session.query(
        db.func.date(User.created_at).label('date'),
        db.func.count(User.id).label('count')
    ).filter(User.created_at >= thirty_days_ago)\
    .group_by(db.func.date(User.created_at))\
    .order_by(db.func.date(User.created_at)).all()
    
    user_reg_dates = [str(row.date) for row in user_registrations]
    user_reg_counts = [row.count for row in user_registrations]
    
    # Get media uploads over time (last 30 days)
    media_uploads = db.session.query(
        db.func.date(Media.created_at).label('date'),
        db.func.count(Media.id).label('count')
    ).filter(Media.created_at >= thirty_days_ago)\
    .group_by(db.func.date(Media.created_at))\
    .order_by(db.func.date(Media.created_at)).all()
    
    media_upload_dates = [str(row.date) for row in media_uploads]
    media_upload_counts = [row.count for row in media_uploads]
    
    return render_template('admin/stats.html',
                           total_users=total_users,
                           admin_users=admin_users,
                           school_coordinators=school_coordinators,
                           volunteers_registered=volunteers_registered,
                           total_articles=total_articles,
                           published_articles=published_articles,
                           total_media=total_media,
                           approved_media=approved_media,
                           total_schools=total_schools,
                           user_reg_dates=json.dumps(user_reg_dates),
                           user_reg_counts=json.dumps(user_reg_counts),
                           media_upload_dates=json.dumps(media_upload_dates),
                           media_upload_counts=json.dumps(media_upload_counts))

@admin.route('/admin/performance-reports')
@login_required
@admin_required
def performance_reports():
    """View and manage performance reports"""
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['PAGINATION_PER_PAGE']
    
    reports = PerformanceReport.query.order_by(PerformanceReport.created_at.desc())\
        .paginate(page=page, per_page=per_page)
    
    return render_template('admin/performance_reports.html', reports=reports)

@admin.route('/admin/performance-reports/new', methods=['GET', 'POST'])
@login_required
@admin_required
def create_performance_report():
    """Create a new performance report"""
    if request.method == 'POST':
        title = request.form.get('title')
        report_period = request.form.get('report_period')
        start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d').date()
        end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%d').date()
        school_id = request.form.get('school_id', type=int)
        is_public = 'is_public' in request.form
        
        if not title or not report_period or not start_date or not end_date:
            flash('All required fields must be filled.', 'danger')
            return redirect(url_for('admin.create_performance_report'))
        
        report = PerformanceReport(
            title=title,
            report_period=report_period,
            start_date=start_date,
            end_date=end_date,
            generated_by=current_user.id,
            school_id=school_id if school_id else None,
            is_public=is_public
        )
        
        db.session.add(report)
        db.session.commit()
        
        # Add sections from form
        section_titles = request.form.getlist('section_title[]')
        section_contents = request.form.getlist('section_content[]')
        
        for i in range(len(section_titles)):
            if section_titles[i] and section_contents[i]:
                report.add_section(section_titles[i], section_contents[i], i)
        
        # Generate PDF
        try:
            pdf_filename = f"report_{report.id}_{datetime.now().strftime('%Y%m%d')}.pdf"
            pdf_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'reports', pdf_filename)
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
            
            # Generate PDF using utility function
            html_content = render_template('reports/pdf_template.html', report=report)
            generate_report_pdf(html_content, pdf_path)
            
            # Update report with PDF path
            report.generate_pdf(pdf_filename)
            
            flash('Performance report created successfully!', 'success')
        except Exception as e:
            current_app.logger.error(f"Error generating PDF: {str(e)}")
            flash('Report created but there was an error generating the PDF.', 'warning')
        
        return redirect(url_for('admin.performance_reports'))
    
    # Get schools for dropdown
    schools = School.query.order_by(School.name).all()
    
    return render_template('admin/create_performance_report.html', schools=schools)

@admin.route('/admin/export-data/<data_type>')
@login_required
@admin_required
def export_data(data_type):
    """Export data to CSV"""
    if data_type == 'users':
        # Export users
        users = User.query.all()
        headers = ['ID', 'Username', 'Email', 'Role', 'Active', 'Created At', 'Last Login']
        data = []
        
        for user in users:
            data.append([
                user.id,
                user.username,
                user.email,
                user.role,
                'Yes' if user.is_active else 'No',
                user.created_at.strftime('%Y-%m-%d %H:%M:%S') if user.created_at else '',
                user.last_login_at.strftime('%Y-%m-%d %H:%M:%S') if user.last_login_at else ''
            ])
        
        filename = f"users_{datetime.now().strftime('%Y%m%d')}.csv"
    
    elif data_type == 'schools':
        # Export schools
        schools = School.query.all()
        headers = ['ID', 'Name', 'Location', 'Student Count', 'Email', 'Phone']
        data = []
        
        for school in schools:
            data.append([
                school.id,
                school.name,
                school.location,
                school.student_count,
                school.email,
                school.phone
            ])
        
        filename = f"schools_{datetime.now().strftime('%Y%m%d')}.csv"
    
    elif data_type == 'volunteers':
        # Export volunteers
        volunteers = Volunteer.query.all()
        headers = ['ID', 'Name', 'Email', 'Phone', 'School', 'Grade', 'Skills', 'Status']
        data = []
        
        for volunteer in volunteers:
            school_name = volunteer.school.name if volunteer.school else 'N/A'
            data.append([
                volunteer.id,
                volunteer.name,
                volunteer.email,
                volunteer.phone,
                school_name,
                volunteer.grade,
                volunteer.skills,
                volunteer.status
            ])
        
        filename = f"volunteers_{datetime.now().strftime('%Y%m%d')}.csv"
    
    elif data_type == 'articles':
        # Export articles
        articles = Article.query.all()
        headers = ['ID', 'Title', 'Category', 'Author', 'Published', 'Views', 'Created At']
        data = []
        
        for article in articles:
            author_name = article.author.username if article.author else 'N/A'
            data.append([
                article.id,
                article.title,
                article.category,
                author_name,
                'Yes' if article.is_published else 'No',
                article.view_count,
                article.created_at.strftime('%Y-%m-%d')
            ])
        
        filename = f"articles_{datetime.now().strftime('%Y%m%d')}.csv"
    
    elif data_type == 'media':
        # Export media
        media_items = Media.query.all()
        headers = ['ID', 'Title', 'Type', 'Creator', 'School', 'Approved', 'Views', 'Created At']
        data = []
        
        for media in media_items:
            creator_name = media.creator.username if media.creator else 'N/A'
            school_name = media.school.name if media.school else 'N/A'
            data.append([
                media.id,
                media.title,
                media.media_type,
                creator_name,
                school_name,
                'Yes' if media.is_approved else 'No',
                media.view_count,
                media.created_at.strftime('%Y-%m-%d')
            ])
        
        filename = f"media_{datetime.now().strftime('%Y%m%d')}.csv"
    
    else:
        flash('Invalid data type for export.', 'danger')
        return redirect(url_for('admin.admin_dashboard'))
    
    # Generate CSV
    csv_data = export_to_csv(headers, data)
    
    # Create response
    response = current_app.response_class(
        csv_data,
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment;filename={filename}'}
    )
    
    return response