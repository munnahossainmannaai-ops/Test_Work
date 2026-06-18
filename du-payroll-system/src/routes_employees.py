from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from src.models import db, Employee, Payroll, Leave, Loan, User
from src.forms import EmployeeForm, PayrollForm, LeaveForm, LoanForm
from datetime import datetime

employees = Blueprint('employees', __name__, url_prefix='/employees')


@employees.route('/')
@login_required
def list_employees():
    """List all employees"""
    if current_user.role not in ['admin', 'hr']:
        flash('Access denied.', 'error')
        return redirect(url_for('main.dashboard'))
    
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    query = Employee.query
    
    if search:
        query = query.filter(
            (Employee.first_name.ilike(f'%{search}%')) |
            (Employee.last_name.ilike(f'%{search}%')) |
            (Employee.employee_id.ilike(f'%{search}%')) |
            (Employee.department.ilike(f'%{search}%'))
        )
    
    pagination = query.order_by(Employee.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('employees/list.html', 
                         employees=pagination.items, 
                         pagination=pagination,
                         search=search)


@employees.route('/add', methods=['GET', 'POST'])
@login_required
def add_employee():
    """Add new employee"""
    if current_user.role not in ['admin', 'hr']:
        flash('Access denied.', 'error')
        return redirect(url_for('main.dashboard'))
    
    form = EmployeeForm()
    
    if form.validate_on_submit():
        # Generate employee ID if not provided
        employee_id = form.employee_id.data
        if not employee_id:
            last_employee = Employee.query.order_by(Employee.id.desc()).first()
            if last_employee:
                last_num = int(last_employee.employee_id.split('-')[-1])
                employee_id = f"DU-EMP-{str(last_num + 1).zfill(3)}"
            else:
                employee_id = "DU-EMP-001"
        
        employee = Employee(
            employee_id=employee_id,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            email=form.email.data,
            phone=form.phone.data,
            date_of_birth=form.date_of_birth.data,
            joining_date=form.joining_date.data,
            department=form.department.data,
            designation=form.designation.data,
            employee_type=form.employee_type.data,
            faculty=form.faculty.data,
            basic_salary=form.basic_salary.data,
            house_rent_allowance=form.house_rent_allowance.data or 0,
            medical_allowance=form.medical_allowance.data or 0,
            transport_allowance=form.transport_allowance.data or 0,
            other_allowances=form.other_allowances.data or 0,
            bank_name=form.bank_name.data,
            bank_account_number=form.bank_account_number.data,
            bank_branch=form.bank_branch.data,
            is_active=form.is_active.data
        )
        
        db.session.add(employee)
        db.session.commit()
        
        flash(f'Employee {employee.full_name} added successfully!', 'success')
        return redirect(url_for('employees.list_employees'))
    
    return render_template('employees/form.html', form=form, title='Add Employee')


@employees.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_employee(id):
    """Edit employee"""
    if current_user.role not in ['admin', 'hr']:
        flash('Access denied.', 'error')
        return redirect(url_for('main.dashboard'))
    
    employee = Employee.query.get_or_404(id)
    form = EmployeeForm(obj=employee)
    
    if form.validate_on_submit():
        employee.first_name = form.first_name.data
        employee.last_name = form.last_name.data
        employee.email = form.email.data
        employee.phone = form.phone.data
        employee.date_of_birth = form.date_of_birth.data
        employee.joining_date = form.joining_date.data
        employee.department = form.department.data
        employee.designation = form.designation.data
        employee.employee_type = form.employee_type.data
        employee.faculty = form.faculty.data
        employee.basic_salary = form.basic_salary.data
        employee.house_rent_allowance = form.house_rent_allowance.data or 0
        employee.medical_allowance = form.medical_allowance.data or 0
        employee.transport_allowance = form.transport_allowance.data or 0
        employee.other_allowances = form.other_allowances.data or 0
        employee.bank_name = form.bank_name.data
        employee.bank_account_number = form.bank_account_number.data
        employee.bank_branch = form.bank_branch.data
        employee.is_active = form.is_active.data
        
        db.session.commit()
        flash(f'Employee {employee.full_name} updated successfully!', 'success')
        return redirect(url_for('employees.list_employees'))
    
    return render_template('employees/form.html', form=form, title='Edit Employee', employee=employee)


@employees.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete_employee(id):
    """Delete employee"""
    if current_user.role not in ['admin', 'hr']:
        flash('Access denied.', 'error')
        return redirect(url_for('main.dashboard'))
    
    employee = Employee.query.get_or_404(id)
    db.session.delete(employee)
    db.session.commit()
    
    flash(f'Employee {employee.full_name} deleted successfully!', 'success')
    return redirect(url_for('employees.list_employees'))


@employees.route('/<int:id>')
@login_required
def view_employee(id):
    """View employee details"""
    employee = Employee.query.get_or_404(id)
    
    # Get employee's payroll history
    payroll_history = Payroll.query.filter_by(employee_id=id).order_by(
        Payroll.year.desc(), Payroll.month.desc()
    ).limit(10).all()
    
    # Get employee's leave records
    leave_records = Leave.query.filter_by(employee_id=id).order_by(
        Leave.applied_date.desc()
    ).limit(10).all()
    
    return render_template('employees/view.html', 
                         employee=employee,
                         payroll_history=payroll_history,
                         leave_records=leave_records)
