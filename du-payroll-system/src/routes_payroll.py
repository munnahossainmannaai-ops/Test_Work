from flask import Blueprint, render_template, redirect, url_for, flash, request, send_file, make_response
from flask_login import login_required, current_user
from src.models import db, Payroll, Employee
from src.forms import PayrollForm
from src.pdf_generator import generate_payslip_pdf
from src.tax_calculator import calculate_tax_for_payroll
from datetime import datetime

payroll = Blueprint('payroll', __name__, url_prefix='/payroll')


@payroll.route('/')
@login_required
def list_payroll():
    """List all payroll records"""
    if current_user.role not in ['admin', 'hr']:
        flash('Access denied.', 'error')
        return redirect(url_for('main.dashboard'))
    
    page = request.args.get('page', 1, type=int)
    month = request.args.get('month', type=int)
    year = request.args.get('year', type=int)
    status = request.args.get('status', '')
    
    query = Payroll.query
    
    if month:
        query = query.filter_by(month=month)
    if year:
        query = query.filter_by(year=year)
    if status:
        query = query.filter_by(payment_status=status)
    
    pagination = query.order_by(Payroll.year.desc(), Payroll.month.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('payroll/list.html', 
                         payroll_records=pagination.items, 
                         pagination=pagination,
                         current_month=month,
                         current_year=year,
                         current_status=status)


@payroll.route('/process', methods=['GET', 'POST'])
@login_required
def process_payroll():
    """Process payroll for an employee"""
    if current_user.role not in ['admin', 'hr']:
        flash('Access denied.', 'error')
        return redirect(url_for('main.dashboard'))
    
    form = PayrollForm()
    
    # Populate employee choices
    employees = Employee.query.filter_by(is_active=True).order_by(Employee.full_name).all()
    form.employee_id.choices = [(emp.id, f"{emp.employee_id} - {emp.full_name}") for emp in employees]
    
    if form.validate_on_submit():
        # Check if payroll already exists for this employee/month/year
        existing = Payroll.query.filter_by(
            employee_id=form.employee_id.data,
            month=form.month.data,
            year=form.year.data
        ).first()
        
        if existing:
            flash('Payroll already exists for this employee in the selected month/year.', 'error')
            return redirect(url_for('payroll.list_payroll'))
        
        employee = Employee.query.get_or_404(form.employee_id.data)
        
        payroll_record = Payroll(
            employee_id=form.employee_id.data,
            month=form.month.data,
            year=form.year.data,
            basic_salary=form.basic_salary.data,
            house_rent_allowance=form.house_rent_allowance.data or 0,
            medical_allowance=form.medical_allowance.data or 0,
            transport_allowance=form.transport_allowance.data or 0,
            other_allowances=form.other_allowances.data or 0,
            overtime_pay=form.overtime_pay.data or 0,
            bonus=form.bonus.data or 0,
            tax_deducted=form.tax_deducted.data or 0,
            provident_fund=form.provident_fund.data or 0,
            gratuity=form.gratuity.data or 0,
            loan_deduction=form.loan_deduction.data or 0,
            other_deductions=form.other_deductions.data or 0,
            payment_status=form.payment_status.data,
            payment_date=form.payment_date.data,
            remarks=form.remarks.data,
            processed_by=current_user.id
        )
        
        # Calculate totals
        payroll_record.calculate_totals()
        
        db.session.add(payroll_record)
        db.session.commit()
        
        flash(f'Payroll processed successfully for {employee.full_name}!', 'success')
        return redirect(url_for('payroll.list_payroll'))
    
    return render_template('payroll/form.html', form=form, title='Process Payroll')


@payroll.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_payroll(id):
    """Edit payroll record"""
    if current_user.role not in ['admin', 'hr']:
        flash('Access denied.', 'error')
        return redirect(url_for('main.dashboard'))
    
    payroll_record = Payroll.query.get_or_404(id)
    form = PayrollForm(obj=payroll_record)
    
    # Populate employee choices
    employees = Employee.query.filter_by(is_active=True).order_by(Employee.full_name).all()
    form.employee_id.choices = [(emp.id, f"{emp.employee_id} - {emp.full_name}") for emp in employees]
    
    if form.validate_on_submit():
        payroll_record.employee_id = form.employee_id.data
        payroll_record.month = form.month.data
        payroll_record.year = form.year.data
        payroll_record.basic_salary = form.basic_salary.data
        payroll_record.house_rent_allowance = form.house_rent_allowance.data or 0
        payroll_record.medical_allowance = form.medical_allowance.data or 0
        payroll_record.transport_allowance = form.transport_allowance.data or 0
        payroll_record.other_allowances = form.other_allowances.data or 0
        payroll_record.overtime_pay = form.overtime_pay.data or 0
        payroll_record.bonus = form.bonus.data or 0
        payroll_record.tax_deducted = form.tax_deducted.data or 0
        payroll_record.provident_fund = form.provident_fund.data or 0
        payroll_record.gratuity = form.gratuity.data or 0
        payroll_record.loan_deduction = form.loan_deduction.data or 0
        payroll_record.other_deductions = form.other_deductions.data or 0
        payroll_record.payment_status = form.payment_status.data
        payroll_record.payment_date = form.payment_date.data
        payroll_record.remarks = form.remarks.data
        
        # Recalculate totals
        payroll_record.calculate_totals()
        
        db.session.commit()
        flash('Payroll record updated successfully!', 'success')
        return redirect(url_for('payroll.list_payroll'))
    
    return render_template('payroll/form.html', form=form, title='Edit Payroll', payroll_record=payroll_record)


@payroll.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete_payroll(id):
    """Delete payroll record"""
    if current_user.role not in ['admin', 'hr']:
        flash('Access denied.', 'error')
        return redirect(url_for('main.dashboard'))
    
    payroll_record = Payroll.query.get_or_404(id)
    db.session.delete(payroll_record)
    db.session.commit()
    
    flash('Payroll record deleted successfully!', 'success')
    return redirect(url_for('payroll.list_payroll'))


@payroll.route('/<int:id>')
@login_required
def view_payroll(id):
    """View payroll details"""
    payroll_record = Payroll.query.get_or_404(id)
    return render_template('payroll/view.html', payroll_record=payroll_record)


@payroll.route('/<int:id>/download-payslip')
@login_required
def download_payslip(id):
    """Download PDF payslip for a payroll record"""
    payroll_record = Payroll.query.get_or_404(id)
    employee = Employee.query.get_or_404(payroll_record.employee_id)
    
    # Check permissions
    if current_user.role not in ['admin', 'hr'] and current_user.id != employee.user_id:
        flash('Access denied.', 'error')
        return redirect(url_for('main.dashboard'))
    
    # Generate PDF
    pdf_content = generate_payslip_pdf(payroll_record, employee)
    
    if pdf_content:
        response = make_response(pdf_content)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=payslip_{employee.employee_id}_{payroll_record.month_name}_{payroll_record.year}.pdf'
        return response
    
    flash('Error generating payslip.', 'error')
    return redirect(url_for('payroll.view_payroll', id=id))


@payroll.route('/process-with-tax', methods=['GET', 'POST'])
@login_required
def process_payroll_with_tax():
    """Process payroll with automatic tax calculation"""
    if current_user.role not in ['admin', 'hr']:
        flash('Access denied.', 'error')
        return redirect(url_for('main.dashboard'))
    
    form = PayrollForm()
    
    # Populate employee choices
    employees = Employee.query.filter_by(is_active=True).order_by(Employee.full_name).all()
    form.employee_id.choices = [(emp.id, f"{emp.employee_id} - {emp.full_name}") for emp in employees]
    
    if form.validate_on_submit():
        # Check if payroll already exists for this employee/month/year
        existing = Payroll.query.filter_by(
            employee_id=form.employee_id.data,
            month=form.month.data,
            year=form.year.data
        ).first()
        
        if existing:
            flash('Payroll already exists for this employee in the selected month/year.', 'error')
            return redirect(url_for('payroll.list_payroll'))
        
        employee = Employee.query.get_or_404(form.employee_id.data)
        
        payroll_record = Payroll(
            employee_id=form.employee_id.data,
            month=form.month.data,
            year=form.year.data,
            basic_salary=form.basic_salary.data,
            house_rent_allowance=form.house_rent_allowance.data or 0,
            medical_allowance=form.medical_allowance.data or 0,
            transport_allowance=form.transport_allowance.data or 0,
            other_allowances=form.other_allowances.data or 0,
            overtime_pay=form.overtime_pay.data or 0,
            bonus=form.bonus.data or 0,
            tax_deducted=0,  # Will be calculated
            provident_fund=form.provident_fund.data or 0,
            gratuity=form.gratuity.data or 0,
            loan_deduction=form.loan_deduction.data or 0,
            other_deductions=form.other_deductions.data or 0,
            payment_status=form.payment_status.data,
            payment_date=form.payment_date.data,
            remarks=form.remarks.data,
            processed_by=current_user.id
        )
        
        # Calculate automatic tax
        calculated_tax = calculate_tax_for_payroll(employee, payroll_record, form.month.data)
        payroll_record.tax_deducted = calculated_tax
        
        # Auto-calculate provident fund if not provided (10% of basic)
        if not form.provident_fund.data:
            payroll_record.provident_fund = form.basic_salary.data * 0.10
        
        # Calculate totals
        payroll_record.calculate_totals()
        
        db.session.add(payroll_record)
        db.session.commit()
        
        flash(f'Payroll processed successfully for {employee.full_name}! Tax calculated: ৳{calculated_tax:,.2f}', 'success')
        return redirect(url_for('payroll.list_payroll'))
    
    return render_template('payroll/form.html', form=form, title='Process Payroll with Auto-Tax', auto_tax=True)
