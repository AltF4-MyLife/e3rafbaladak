from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, abort
from flask_login import login_required, current_user
from app.models.volunteer import Volunteer, Contribution
from app.models.school import School
from app.forms import VolunteerForm
from app import db
from app.utils import send_volunteer_thank_you_email, export_to_csv
from datetime import datetime

volunteers = Blueprint('volunteer', __name__)

@volunteers.route('/volunteers')
def volunteers_list():
    """List all volunteers (admin only)"""
    if not current_user.is_authenticated or not current_user.is_admin():
        flash('You do not have permission to view all volunteers.', 'danger')
        return redirect(url_for('main.index'))
    
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['PAGINATION_PER_PAGE']
    
    volunteers = Volunteer.query.order_by(Volunteer.created_at.desc()).paginate(page=page, per_page=per_page)
    
    return render_template('volunteers/list.html', volunteers=volunteers)

@volunteers.route('/schools/<int:school_id>/volunteers')
@login_required
def school_volunteers(school_id):
    """List volunteers for a specific school"""
    school = School.query.get_or_404(school_id)
    
    # Only admins or school coordinators can view school volunteers
    if not (current_user.is_admin() or current_user.is_school_coordinator(school.id)):
        flash('You do not have permission to view volunteers for this school.', 'danger')
        return redirect(url_for('school.school_detail', id=school.id))
    
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['PAGINATION_PER_PAGE']
    
    volunteers = Volunteer.query.filter_by(school_id=school.id)\
        .order_by(Volunteer.created_at.desc()).paginate(page=page, per_page=per_page)
    
    return render_template('volunteers/school_volunteers.html', 
                           school=school, volunteers=volunteers)

@volunteers.route('/volunteer/register', methods=['GET', 'POST'])
def volunteer_register():
    """Register as a volunteer"""
    form = VolunteerForm()
    
    # Get schools for dropdown
    schools = School.query.order_by(School.name).all()
    form.school_id.choices = [(s.id, s.name) for s in schools]
    
    if form.validate_on_submit():
        # Check if volunteer with this email already exists
        existing_volunteer = Volunteer.query.filter_by(email=form.email.data).first()
        if existing_volunteer:
            flash('A volunteer with this email already exists.', 'danger')
            return redirect(url_for('volunteer.volunteer_register'))
        
        volunteer = Volunteer(
            name=form.name.data,
            email=form.email.data,
            phone=form.phone.data,
            school_id=form.school_id.data,
            grade=form.grade.data,
            skills=','.join(form.skills.data),  # Convert list to comma-separated string
            availability=form.availability.data,
            experience=form.experience.data
        )
        
        db.session.add(volunteer)
        db.session.commit()
        
        # Send thank you email
        try:
            send_volunteer_thank_you_email(volunteer)
            flash('Thank you for registering as a volunteer! Check your email for confirmation.', 'success')
        except Exception as e:
            current_app.logger.error(f"Error sending thank you email: {str(e)}")
            flash('Thank you for registering as a volunteer! There was an issue sending the confirmation email.', 'success')
        
        return redirect(url_for('main.index'))
    
    return render_template('volunteers/register.html', form=form)

@volunteers.route('/volunteers/<int:id>')
@login_required
def volunteer_detail(id):
    """Show volunteer details"""
    volunteer = Volunteer.query.get_or_404(id)
    
    # Only admins, school coordinators of the volunteer's school, or the volunteer themselves can view details
    if not (current_user.is_admin() or 
            (volunteer.school_id and current_user.is_school_coordinator(volunteer.school_id)) or 
            (current_user.is_authenticated and current_user.email == volunteer.email)):
        flash('You do not have permission to view this volunteer profile.', 'danger')
        return redirect(url_for('main.index'))
    
    # Get contributions
    contributions = Contribution.query.filter_by(volunteer_id=volunteer.id)\
        .order_by(Contribution.timestamp.desc()).all()
    
    return render_template('volunteers/detail.html', volunteer=volunteer, contributions=contributions)

@volunteers.route('/volunteers/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def volunteer_edit(id):
    """Edit a volunteer"""
    volunteer = Volunteer.query.get_or_404(id)
    
    # Only admins, school coordinators of the volunteer's school, or the volunteer themselves can edit
    if not (current_user.is_admin() or 
            (volunteer.school_id and current_user.is_school_coordinator(volunteer.school_id)) or 
            (current_user.is_authenticated and current_user.email == volunteer.email)):
        flash('You do not have permission to edit this volunteer profile.', 'danger')
        return redirect(url_for('volunteers.volunteer_detail', id=volunteer.id))
    
    form = VolunteerForm(obj=volunteer)
    
    # Get schools for dropdown
    schools = School.query.order_by(School.name).all()
    form.school_id.choices = [(s.id, s.name) for s in schools]
    
    # Convert comma-separated skills to list for form
    if volunteer.skills:
        form.skills.data = volunteer.skills.split(',')
    
    if form.validate_on_submit():
        volunteer.name = form.name.data
        volunteer.email = form.email.data
        volunteer.phone = form.phone.data
        volunteer.school_id = form.school_id.data
        volunteer.grade = form.grade.data
        volunteer.skills = ','.join(form.skills.data)  # Convert list to comma-separated string
        volunteer.availability = form.availability.data
        volunteer.experience = form.experience.data
        
        db.session.commit()
        
        flash('Volunteer profile updated successfully!', 'success')
        return redirect(url_for('volunteers.volunteer_detail', id=volunteer.id))
    
    return render_template('volunteers/edit.html', form=form, volunteer=volunteer)

@volunteers.route('/volunteers/<int:id>/status/<status>', methods=['POST'])
@login_required
def volunteer_update_status(id, status):
    """Update volunteer status (admin only)"""
    if not current_user.is_admin():
        flash('You do not have permission to update volunteer status.', 'danger')
        return redirect(url_for('volunteers.volunteer_detail', id=id))
    
    volunteer = Volunteer.query.get_or_404(id)
    
    if status == 'active':
        volunteer.status = 'active'
        flash('Volunteer status updated to active.', 'success')
    elif status == 'inactive':
        volunteer.status = 'inactive'
        flash('Volunteer status updated to inactive.', 'success')
    else:
        flash('Invalid status.', 'danger')
    
    db.session.commit()
    return redirect(url_for('volunteers.volunteer_detail', id=id))

@volunteers.route('/volunteers/export')
@login_required
def export_volunteers():
    """Export volunteers to CSV (admin only)"""
    if not current_user.is_admin():
        flash('You do not have permission to export volunteers.', 'danger')
        return redirect(url_for('volunteers.volunteers_list'))
    
    # Get filter parameters
    school_id = request.args.get('school_id', type=int)
    status = request.args.get('status')
    
    # Build query
    query = Volunteer.query
    
    if school_id:
        query = query.filter_by(school_id=school_id)
    
    if status:
        query = query.filter_by(status=status)
    
    volunteers = query.all()
    
    # Prepare data for CSV
    data = []
    headers = ['ID', 'Name', 'Email', 'Phone', 'School', 'Grade', 'Skills', 'Status', 'Registered On']
    
    for v in volunteers:
        school_name = v.school.name if v.school else 'N/A'
        data.append([
            v.id,
            v.name,
            v.email,
            v.phone,
            school_name,
            v.grade,
            v.skills,
            v.status,
            v.created_at.strftime('%Y-%m-%d')
        ])
    
    # Generate CSV
    csv_data = export_to_csv(headers, data)
    
    # Create response
    response = current_app.response_class(
        csv_data,
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment;filename=volunteers_{datetime.now().strftime("%Y%m%d")}.csv'}
    )
    
    return response

@volunteers.route('/volunteers/<int:id>/add-contribution', methods=['POST'])
@login_required
def add_contribution(id):
    """Add a contribution record for a volunteer"""
    volunteer = Volunteer.query.get_or_404(id)
    
    # Only admins or school coordinators of the volunteer's school can add contributions
    if not (current_user.is_admin() or 
            (volunteer.school_id and current_user.is_school_coordinator(volunteer.school_id))):
        flash('You do not have permission to add contributions for this volunteer.', 'danger')
        return redirect(url_for('volunteer.volunteer_detail', id=id))
    
    contribution_type = request.form.get('contribution_type')
    item_id = request.form.get('item_id')
    description = request.form.get('description')
    
    if not contribution_type or not description:
        flash('Contribution type and description are required.', 'danger')
        return redirect(url_for('volunteer.volunteer_detail', id=id))
    
    contribution = Contribution(
        volunteer_id=volunteer.id,
        contribution_type=contribution_type,
        item_id=item_id,
        description=description
    )
    
    db.session.add(contribution)
    db.session.commit()
    
    flash('Contribution added successfully!', 'success')
    return redirect(url_for('volunteers.volunteer_detail', id=id))