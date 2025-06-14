from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify, session
from flask_login import login_required, current_user
from app.models.article import Article
from app.models.media import Media
from app.models.school import School
from app.models.volunteer import Volunteer
from app.forms import ContactForm, SearchForm
from app import db
from app.utils import send_email
import os

main = Blueprint('main', __name__)

@main.route('/')
def index():
    """Homepage route"""
    # Get featured articles
    featured_articles = Article.query.filter_by(
        is_published=True
    ).order_by(Article.published_at.desc()).limit(3).all()
    
    # Get featured media
    featured_media = Media.query.filter_by(
        is_approved=True,
        featured=True
    ).order_by(Media.created_at.desc()).limit(4).all()
    
    # Get school count
    school_count = School.query.count()
    
    # Get volunteer count
    volunteer_count = Volunteer.query.count()
    
    # Get article count
    article_count = Article.query.filter_by(is_published=True).count()
    
    # Get media count
    media_count = Media.query.filter_by(is_approved=True).count()
    
    return render_template('index.html', 
                           featured_articles=featured_articles,
                           featured_media=featured_media,
                           school_count=school_count,
                           volunteer_count=volunteer_count,
                           article_count=article_count,
                           media_count=media_count)

@main.route('/about')
def about():
    """About page route"""
    return render_template('about.html')

@main.route('/contact', methods=['GET', 'POST'])
def contact():
    """Contact page route"""
    form = ContactForm()
    if form.validate_on_submit():
        # Send email to support
        subject = f"[e3rafbaladak] Contact Form: {form.subject.data}"
        body = f"From: {form.name.data} <{form.email.data}>\n\n{form.message.data}"
        
        try:
            send_email(
                subject=subject,
                sender=current_app.config['MAIL_DEFAULT_SENDER'],
                recipients=[current_app.config['SUPPORT_EMAIL']],
                text_body=body,
                html_body=f"<p>From: {form.name.data} &lt;{form.email.data}&gt;</p><p>{form.message.data}</p>"
            )
            flash('Your message has been sent. Thank you!', 'success')
            return redirect(url_for('main.contact'))
        except Exception as e:
            current_app.logger.error(f"Error sending contact email: {str(e)}")
            flash('An error occurred while sending your message. Please try again later.', 'danger')
    
    return render_template('contact.html', form=form)

@main.route('/search')
def search():
    """Search results page"""
    form = SearchForm(request.args, meta={'csrf': False})
    results = {}
    
    if form.validate():
        query = form.query.data
        category = form.category.data
        
        # Search in articles
        if category in ['all', 'articles']:
            articles = Article.query.filter(
                Article.is_published == True,
                (Article.title.ilike(f'%{query}%') | Article.content.ilike(f'%{query}%'))
            ).all()
            results['articles'] = articles
        
        # Search in schools
        if category in ['all', 'schools']:
            schools = School.query.filter(
                School.name.ilike(f'%{query}%') | School.description.ilike(f'%{query}%')
            ).all()
            results['schools'] = schools
        
        # Search in media
        if category in ['all', 'media']:
            media = Media.query.filter(
                Media.is_approved == True,
                (Media.title.ilike(f'%{query}%') | Media.description.ilike(f'%{query}%'))
            ).all()
            results['media'] = media
    
    return render_template('search_results.html', form=form, results=results, query=form.query.data)

@main.route('/language/<lang_code>')
def set_language(lang_code):
    """Set the user's preferred language"""
    # Store the language preference in session
    session['language'] = lang_code
    
    # Redirect back to the referring page or home
    next_url = request.referrer or url_for('main.index')
    return redirect(next_url)

@main.route('/sitemap')
def sitemap():
    """Sitemap page"""
    return render_template('sitemap.html')

@main.route('/terms')
def terms():
    """Terms and conditions page"""
    return render_template('terms.html')

@main.route('/privacy')
def privacy():
    """Privacy policy page"""
    return render_template('privacy.html')

@main.route('/faq')
def faq():
    """Frequently asked questions page"""
    return render_template('faq.html')

@main.route('/error-test/<error_code>')
def error_test(error_code):
    """Test error pages (for development only)"""
    if current_app.config['ENV'] != 'development':
        return redirect(url_for('main.index'))
    
    try:
        error_code = int(error_code)
        if error_code == 404:
            return render_template('errors/404.html'), 404
        elif error_code == 403:
            return render_template('errors/403.html'), 403
        elif error_code == 500:
            return render_template('errors/500.html'), 500
        else:
            return f"Unknown error code: {error_code}"
    except ValueError:
        return f"Invalid error code: {error_code}"