import os
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate
from flask_babel import Babel
from flask_wtf.csrf import CSRFProtect
from flask_bootstrap import Bootstrap

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()
migrate = Migrate()
babel = Babel()
csrf = CSRFProtect()
bootstrap = Bootstrap()

def get_locale():
    # Default to Arabic
    return 'ar'

def create_app(config_class=None):
    app = Flask(__name__)
    
    # Load configuration
    if config_class is None:
        app.config.from_object('app.config.Config')
    else:
        app.config.from_object(config_class)
    
    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'
    login_manager.login_message = 'يرجى تسجيل الدخول للوصول إلى هذه الصفحة'
    
    mail.init_app(app)
    migrate.init_app(app, db)
    babel.init_app(app, locale_selector=get_locale)
    csrf.init_app(app)
    bootstrap.init_app(app)
    
    # Ensure upload directories exist
    os.makedirs(os.path.join(app.static_folder, 'uploads', 'school_logos'), exist_ok=True)
    os.makedirs(os.path.join(app.static_folder, 'uploads', 'media'), exist_ok=True)
    os.makedirs(os.path.join(app.static_folder, 'uploads', 'reports'), exist_ok=True)
    
    # Register blueprints
    from app.routes.main_routes import main
    from app.routes.school_routes import schools
    from app.routes.volunteer_routes import volunteers
    from app.routes.admin_routes import admin
    from app.routes.content_routes import content
    from app.routes.auth_routes import auth
    
    app.register_blueprint(main)
    app.register_blueprint(schools, url_prefix='/schools')
    app.register_blueprint(volunteers, url_prefix='/volunteers')
    app.register_blueprint(admin, url_prefix='/admin')
    app.register_blueprint(content, url_prefix='/content')
    app.register_blueprint(auth, url_prefix='/auth')
    
    # Error handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('errors/500.html'), 500
    
    # Import models to ensure they are registered with SQLAlchemy
    from app.models import user, school, volunteer, article, media, report
    
    # Shell context processor
    @app.shell_context_processor
    def make_shell_context():
        return {
            'db': db, 
            'User': user.User, 
            'School': school.School,
            'Volunteer': volunteer.Volunteer,
            'Article': article.Article,
            'Media': media.Media,
            'Report': report.Report
        }
    
    # Template context processor to add common variables to all templates
    @app.context_processor
    def inject_now():
        from datetime import datetime
        return {'now': datetime.utcnow()}
    
    return app