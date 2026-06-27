from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from .models import db, User, Employee, Payroll, Loan, Attendance
from datetime import datetime
import json

main_bp = Blueprint('main', __name__)

# Authentication Blueprint
auth_bp = Blueprint('auth', __name__, template_folder='templates/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            if not user.is_active:
                flash('Your account has been deactivated. Please contact admin.', 'danger')
                return render_template('auth/login.html')
            
            login_user(user)
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            next_page = request.args.get('next')
            flash(f'Welcome back, {user.username}!', 'success')
            return redirect(next_page or url_for('main.dashboard'))
        
        flash('Invalid username or password.', 'danger')
    
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth.login'))

# Main Routes
@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('auth.login'))

@main_bp.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard with statistics"""
    stats = {
        'total_employees': Employee.query.filter_by(status='Active').count(),
        'pending_loans': Loan.query.filter_by(status='Pending').count(),
        'monthly_payroll': Payroll.query.filter_by(
            month=datetime.now().strftime('%B'),
            year=datetime.now().year
        ).count(),
        'total_attendance_today': Attendance.query.filter_by(
            date=datetime.today().date(),
            status='Present'
        ).count()
    }
    
    recent_payrolls = Payroll.query.order_by(Payroll.generated_at.desc()).limit(5).all()
    recent_loans = Loan.query.order_by(Loan.application_date.desc()).limit(5).all()
    
    return render_template('dashboard/index.html', 
                         stats=stats, 
                         recent_payrolls=recent_payrolls,
                         recent_loans=recent_loans)

@main_bp.route('/employees')
@login_required
def employees():
    """Employee list view"""
    if current_user.role not in ['Admin', 'HR']:
        flash('Access denied.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    employees = Employee.query.all()
    return render_template('dashboard/employees.html', employees=employees)

@main_bp.route('/payroll')
@login_required
def payroll_list():
    """Payroll records view"""
    if current_user.role not in ['Admin', 'HR', 'Accounts']:
        flash('Access denied.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    payrolls = Payroll.query.order_by(Payroll.generated_at.desc()).all()
    return render_template('payroll/list.html', payrolls=payrolls)

@main_bp.route('/api/stats')
@login_required
def get_stats():
    """API endpoint for dashboard statistics"""
    stats = {
        'total_employees': Employee.query.filter_by(status='Active').count(),
        'pending_loans': Loan.query.filter_by(status='Pending').count(),
        'active_grants': 0,  # Would need ResearchGrant model query
        'attendance_rate': 0  # Would need calculation
    }
    return jsonify(stats)

# Register blueprints
def register_blueprints(app):
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
