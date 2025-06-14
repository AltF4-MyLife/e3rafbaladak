from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, abort
from flask_login import login_required, current_user
from app.models.school import School, Activity
from app.models.report import Report
from app.models.user import User
from app.forms import SchoolForm, ActivityForm, ReportForm
from app import db
from app.utils import save_file, allowed_file, export_to_csv
from werkzeug.utils import secure_filename
import os
from datetime import datetime

schools = Blueprint('school', __name__)

@schools.route('/schools')
def schools_list():
    """List all schools"""
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['PAGINATION_PER_PAGE']
    
    schools = School.query.order_by(School.name).paginate(page=page, per_page=per_page)
    
    return render_template('schools/list.html', schools=schools)

@schools.route('/schools/<int:id>')
def school_detail(id):
    """Show school details"""
    school = School.query.get_or_404(id)
    
    # Get recent activities
    activities = Activity.query.filter_by(school_id=school.id)\
        .order_by(Activity.date.desc()).limit(5).all()
    
    return render_template('schools/detail.html', school=school, activities=activities)

@schools.route('/schools/new', methods=['GET', 'POST'])
@login_required
def school_create():
    """Create a new school"""
    # Only admins can create schools
    if not current_user.is_admin():
        flash('You do not have permission to create schools.', 'danger')
        return redirect(url_for('schools.schools_list'))
    
    form = SchoolForm()
    if form.validate_on_submit():
        school = School(
            name=form.name.data,
            location=form.location.data,
            address=form.address.data,
            phone=form.phone.data,
            email=form.email.data,
            website=form.website.data,
            description=form.description.data,
            student_count=form.student_count.data
        )
        
        # Handle logo upload
        if form.logo.data:
            logo_filename = save_file(form.logo.data, 'schools')
            if logo_filename:
                school.logo = logo_filename
        
        db.session.add(school)
        db.session.commit()
        
        flash('School created successfully!', 'success')
        return redirect(url_for('school.school_detail', id=school.id))
    
    return render_template('schools/form.html', form=form, title='Create School')

@schools.route('/schools/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def school_edit(id):
    """Edit a school"""
    school = School.query.get_or_404(id)
    
    # Only admins or school coordinators can edit schools
    if not (current_user.is_admin() or current_user.is_school_coordinator(school.id)):
        flash('You do not have permission to edit this school.', 'danger')
        return redirect(url_for('school.school_detail', id=school.id))
    
    form = SchoolForm(obj=school)
    if form.validate_on_submit():
        school.name = form.name.data
        school.location = form.location.data
        school.address = form.address.data
        school.phone = form.phone.data
        school.email = form.email.data
        school.website = form.website.data
        school.description = form.description.data
        school.student_count = form.student_count.data
        
        # Handle logo upload
        if form.logo.data:
            logo_filename = save_file(form.logo.data, 'schools')
            if logo_filename:
                # Delete old logo if exists
                if school.logo:
                    old_logo_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'schools', school.logo)
                    if os.path.exists(old_logo_path):
                        os.remove(old_logo_path)
                
                school.logo = logo_filename
        
        db.session.commit()
        
        flash('School updated successfully!', 'success')
        return redirect(url_for('school.school_detail', id=school.id))
    
    return render_template('schools/form.html', form=form, school=school, title='Edit School')

@schools.route('/schools/<int:id>/activities')
def school_activities(id):
    """List all activities for a school"""
    school = School.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['PAGINATION_PER_PAGE']
    
    activities = Activity.query.filter_by(school_id=school.id)\
        .order_by(Activity.date.desc()).paginate(page=page, per_page=per_page)
    
    return render_template('schools/activities.html', school=school, activities=activities)

@schools.route('/schools/<int:id>/activities/new', methods=['GET', 'POST'])
@login_required
def activity_create(id):
    """Create a new activity for a school"""
    school = School.query.get_or_404(id)
    
    # Only admins or school coordinators can create activities
    if not (current_user.is_admin() or current_user.is_school_coordinator(school.id)):
        flash('You do not have permission to create activities for this school.', 'danger')
        return redirect(url_for('schools.school_activities', id=school.id))
    
    form = ActivityForm()
    if form.validate_on_submit():
        activity = Activity(
            title=form.title.data,
            description=form.description.data,
            date=form.date.data,
            location=form.location.data,
            school_id=school.id,
            created_by=current_user.id,
            status=form.status.data
        )
        
        db.session.add(activity)
        db.session.commit()
        
        flash('Activity created successfully!', 'success')
        return redirect(url_for('schools.school_activities', id=school.id))
    
    return render_template('schools/activity_form.html', form=form, school=school, title='Create Activity')

@schools.route('/activities/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def activity_edit(id):
    """Edit an activity"""
    activity = Activity.query.get_or_404(id)
    school = School.query.get_or_404(activity.school_id)
    
    # Only admins, school coordinators, or the creator can edit activities
    if not (current_user.is_admin() or current_user.is_school_coordinator(school.id) or 
            activity.created_by == current_user.id):
        flash('You do not have permission to edit this activity.', 'danger')
        return redirect(url_for('school.school_detail', id=school.id))
    
    form = ActivityForm(obj=activity)
    if form.validate_on_submit():
        activity.title = form.title.data
        activity.description = form.description.data
        activity.date = form.date.data
        activity.location = form.location.data
        activity.status = form.status.data
        
        db.session.commit()
        
        flash('Activity updated successfully!', 'success')
        return redirect(url_for('school.school_activities', id=school.id))
    
    return render_template('schools/activity_form.html', form=form, school=school, 
                           activity=activity, title='Edit Activity')

@schools.route('/activities/<int:id>')
def activity_detail(id):
    """Show activity details"""
    activity = Activity.query.get_or_404(id)
    school = School.query.get_or_404(activity.school_id)
    
    return render_template('schools/activity_detail.html', activity=activity, school=school)

@schools.route('/schools/<int:id>/reports')
@login_required
def school_reports(id):
    """List all reports for a school"""
    school = School.query.get_or_404(id)
    
    # Only admins or school coordinators can view reports
    if not (current_user.is_admin() or current_user.is_school_coordinator(school.id)):
        flash('You do not have permission to view reports for this school.', 'danger')
        return redirect(url_for('school.school_detail', id=school.id))
    
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['PAGINATION_PER_PAGE']
    
    reports = Report.query.filter_by(school_id=school.id)\
        .order_by(Report.created_at.desc()).paginate(page=page, per_page=per_page)
    
    return render_template('schools/reports.html', school=school, reports=reports)

@schools.route('/schools/<int:id>/reports/new', methods=['GET', 'POST'])
@login_required
def report_create(id):
    """Create a new report for a school"""
    school = School.query.get_or_404(id)
    
    # Only admins or school coordinators can create reports
    if not (current_user.is_admin() or current_user.is_school_coordinator(school.id)):
        flash('You do not have permission to create reports for this school.', 'danger')
        return redirect(url_for('schools.school_reports', id=school.id))
    
    form = ReportForm()
    
    # Get activities for this school for the dropdown
    activities = Activity.query.filter_by(school_id=school.id).all()
    form.activity_id.choices = [(0, 'None')] + [(a.id, a.title) for a in activities]
    
    if form.validate_on_submit():
        report = Report(
            title=form.title.data,
            description=form.description.data,
            report_type=form.report_type.data,
            school_id=school.id,
            submitted_by=current_user.id,
            activity_id=form.activity_id.data if form.activity_id.data != 0 else None
        )
        
        db.session.add(report)
        db.session.commit()
        
        # Handle attachments
        for attachment in form.attachments.data:
            if attachment and allowed_file(attachment.filename):
                attachment_filename = save_file(attachment, 'reports')
                if attachment_filename:
                    file_type = attachment.filename.rsplit('.', 1)[1].lower()
                    report.add_attachment(attachment_filename, file_type)
        
        # Add metrics if provided
        if form.student_count.data:
            report.add_metric('student_count', str(form.student_count.data), 'students')
        
        if form.volunteer_count.data:
            report.add_metric('volunteer_count', str(form.volunteer_count.data), 'volunteers')
        
        flash('Report submitted successfully!', 'success')
        return redirect(url_for('school.school_detail', id=school.id))
    
    return render_template('schools/report_form.html', form=form, school=school, title='Submit Report')

@schools.route('/reports/<int:id>')
@login_required
def report_detail(id):
    """Show report details"""
    report = Report.query.get_or_404(id)
    school = School.query.get_or_404(report.school_id)
    
    # Only admins, school coordinators, or the submitter can view reports
    if not (current_user.is_admin() or current_user.is_school_coordinator(school.id) or 
            report.submitted_by == current_user.id):
        flash('You do not have permission to view this report.', 'danger')
        return redirect(url_for('schools.school_detail', id=school.id))
    
    return render_template('schools/report_detail.html', report=report, school=school)

@schools.route('/schools/export')
@login_required
def schools_export():
    """Export schools to CSV"""
    if not current_user.is_admin():
        flash('You do not have permission to export schools.', 'danger')
        return redirect(url_for('schools.schools_list'))
    
    schools = School.query.all()
    
    # Prepare data for CSV
    data = []
    headers = ['ID', 'Name', 'Location', 'Address', 'Phone', 'Email', 'Website', 'Student Count']
    
    for school in schools:
        data.append([
            school.id,
            school.name,
            school.location,
            school.address,
            school.phone,
            school.email,
            school.website,
            school.student_count
        ])
    
    # Generate CSV
    csv_data = export_to_csv(headers, data)
    
    # Create response
    response = current_app.response_class(
        csv_data,
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment;filename=schools_{datetime.now().strftime("%Y%m%d")}.csv'}
    )
    
    return response

@schools.route('/schools/<int:id>/coordinators')
@login_required
def school_coordinators(id):
    """List coordinators for a school"""
    school = School.query.get_or_404(id)
    
    # Only admins or school coordinators can view coordinators
    if not (current_user.is_admin() or current_user.is_school_coordinator(school.id)):
        flash('You do not have permission to view coordinators for this school.', 'danger')
        return redirect(url_for('schools.school_detail', id=school.id))
    
    # Get users with school coordinator role for this school
    coordinators = User.query.filter(
        User.role == 'school_coordinator',
        User.school_id == school.id
    ).all()
    
    return render_template('schools/coordinators.html', school=school, coordinators=coordinators)