from flask import Flask, render_template
from config import Config
from src.models import db, login_manager, User, Employee, Payroll, Leave, Loan, AuditLog
from src.routes import main
from src.routes_employees import employees
from src.routes_payroll import payroll
from src.routes_leaves import leaves
from src.routes_loans import loans
from src.routes_reports import reports
from src.forms import LoginForm, RegistrationForm


def create_app(config_class=Config):
    """Application factory"""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    
    # Register blueprints
    app.register_blueprint(main)
    app.register_blueprint(employees)
    app.register_blueprint(payroll)
    app.register_blueprint(leaves)
    app.register_blueprint(loans)
    app.register_blueprint(reports)
    
    # Create database tables
    with app.app_context():
        db.create_all()
        
        # Create default admin user if not exists
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@du.ac.bd',
                role='admin',
                is_active=True
            )
            admin.set_password('admin123')
            db.session.add(admin)
            
            # Create admin employee record
            admin_employee = Employee(
                employee_id='DU-ADMIN-001',
                first_name='System',
                last_name='Administrator',
                email='admin@du.ac.bd',
                department='Administration',
                designation='System Administrator',
                employee_type='Permanent',
                basic_salary=50000.0,
                house_rent_allowance=15000.0,
                medical_allowance=5000.0,
                transport_allowance=3000.0,
                joining_date='2024-01-01'
            )
            admin.user = admin_employee
            db.session.commit()
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500
    
    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
