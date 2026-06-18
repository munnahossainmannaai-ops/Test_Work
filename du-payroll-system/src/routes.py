from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from src.models import db, User, Employee
from src.forms import LoginForm, RegistrationForm

main = Blueprint('main', __name__)


@main.route('/')
def index():
    """Home page"""
    return render_template('index.html')


@main.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        
        if user and user.check_password(form.password.data) and user.is_active:
            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get('next')
            flash('Login successful!', 'success')
            return redirect(next_page or url_for('main.dashboard'))
        else:
            flash('Invalid username or password.', 'error')
    
    return render_template('login.html', form=form)


@main.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))


@main.route('/dashboard')
@login_required
def dashboard():
    """Dashboard with overview"""
    # Get statistics
    total_employees = Employee.query.filter_by(is_active=True).count()
    
    # Get recent payroll records
    recent_payroll = []
    if current_user.role in ['admin', 'hr']:
        recent_payroll = db.session.query(Payroll).order_by(Payroll.created_at.desc()).limit(5).all()
    
    # Get pending leaves
    pending_leaves = []
    if current_user.role in ['admin', 'hr']:
        pending_leaves = Leave.query.filter_by(status='pending').count()
    
    return render_template('dashboard.html', 
                         total_employees=total_employees,
                         recent_payroll=recent_payroll,
                         pending_leaves=pending_leaves)


@main.route('/profile')
@login_required
def profile():
    """User profile page"""
    employee = None
    if hasattr(current_user, 'employee'):
        employee = current_user.employee
    
    return render_template('profile.html', employee=employee)
