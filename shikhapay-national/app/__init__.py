from flask import Flask
from .config import Config
from .models import db
from flask_login import LoginManager
from flask_migrate import Migrate
import os

def create_app(config_class=Config):
    """Application factory for ShikkhaPay"""
    
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Ensure instance folder exists
    os.makedirs(os.path.join(app.instance_path), exist_ok=True)
    os.makedirs(app.config.get('UPLOAD_FOLDER', 'app/static/uploads'), exist_ok=True)
    
    # Initialize extensions
    db.init_app(app)
    migrate = Migrate(app, db)
    
    # Setup Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'
    
    from .models import User
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Register blueprints
    from .routes import main_bp
    app.register_blueprint(main_bp)
    
    # Create database tables and seed data
    with app.app_context():
        db.create_all()
        
        # Create default admin user if not exists
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin', role='Admin')
            admin.set_password('admin123')
            db.session.add(admin)
            
            # Create sample employee for admin
            from .models import Employee
            emp = Employee(
                employee_code='DU001',
                name="Dr. Admin User",
                designation="Professor",
                department="Computer Science & Engineering",
                basic_salary=80000,
                email="admin@du.ac.bd",
                phone="+8801700000000",
                bank_account="1234567890",
                bank_name="Sonali Bank"
            )
            db.session.add(emp)
            db.session.commit()
            
            admin.employee_id = emp.id
            db.session.commit()
            
            print("✅ Default admin user created: admin / admin123")
        
        # Create HR user if not exists
        if not User.query.filter_by(username='hr').first():
            hr_user = User(username='hr', role='HR')
            hr_user.set_password('hr123')
            db.session.add(hr_user)
            db.session.commit()
            print("✅ Default HR user created: hr / hr123")
    
    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return "Page Not Found - ShikkhaPay", 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return "Internal Server Error - ShikkhaPay", 500
    
    return app
