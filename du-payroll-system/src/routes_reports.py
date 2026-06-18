from flask import Blueprint, render_template, redirect, url_for, flash, request, make_response
from flask_login import login_required, current_user
from src.models import db, Employee, Payroll, Leave, Loan
from datetime import datetime
import io

reports = Blueprint('reports', __name__, url_prefix='/reports')


@reports.route('/')
@login_required
def index():
    """Reports dashboard"""
    if current_user.role not in ['admin', 'hr']:
        flash('Access denied.', 'error')
        return redirect(url_for('main.dashboard'))
    
    # Get summary statistics
    total_employees = Employee.query.filter_by(is_active=True).count()
    total_payroll_this_month = Payroll.query.filter_by(
        month=datetime.now().month,
        year=datetime.now().year
    ).count()
    
    pending_leaves = Leave.query.filter_by(status='pending').count()
    active_loans = Loan.query.filter_by(status='active').count()
    
    return render_template('reports/index.html',
                         total_employees=total_employees,
                         total_payroll_this_month=total_payroll_this_month,
                         pending_leaves=pending_leaves,
                         active_loans=active_loans)


@reports.route('/payroll-summary')
@login_required
def payroll_summary():
    """Payroll summary report"""
    if current_user.role not in ['admin', 'hr']:
        flash('Access denied.', 'error')
        return redirect(url_for('main.dashboard'))
    
    month = request.args.get('month', datetime.now().month, type=int)
    year = request.args.get('year', datetime.now().year, type=int)
    
    payroll_records = Payroll.query.filter_by(month=month, year=year).all()
    
    # Calculate totals
    total_gross = sum(r.gross_pay for r in payroll_records)
    total_deductions = sum(r.total_deductions for r in payroll_records)
    total_net = sum(r.net_pay for r in payroll_records)
    
    return render_template('reports/payroll_summary.html',
                         payroll_records=payroll_records,
                         month=month,
                         year=year,
                         total_gross=total_gross,
                         total_deductions=total_deductions,
                         total_net=total_net)


@reports.route('/employee-summary')
@login_required
def employee_summary():
    """Employee summary report"""
    if current_user.role not in ['admin', 'hr']:
        flash('Access denied.', 'error')
        return redirect(url_for('main.dashboard'))
    
    department = request.args.get('department', '')
    
    query = Employee.query.filter_by(is_active=True)
    if department:
        query = query.filter_by(department=department)
    
    employees = query.order_by(Employee.department, Employee.designation).all()
    
    # Get unique departments for filter
    departments = db.session.query(Employee.department).distinct().all()
    departments = [d[0] for d in departments if d[0]]
    
    return render_template('reports/employee_summary.html',
                         employees=employees,
                         departments=departments,
                         selected_department=department)


@reports.route('/leave-report')
@login_required
def leave_report():
    """Leave report"""
    if current_user.role not in ['admin', 'hr']:
        flash('Access denied.', 'error')
        return redirect(url_for('main.dashboard'))
    
    status = request.args.get('status', '')
    leave_type = request.args.get('leave_type', '')
    
    query = Leave.query
    
    if status:
        query = query.filter_by(status=status)
    if leave_type:
        query = query.filter_by(leave_type=leave_type)
    
    leaves = query.order_by(Leave.applied_date.desc()).all()
    
    # Summary statistics
    total_leaves = len(leaves)
    approved = Leave.query.filter_by(status='approved').count()
    pending = Leave.query.filter_by(status='pending').count()
    rejected = Leave.query.filter_by(status='rejected').count()
    
    return render_template('reports/leave_report.html',
                         leaves=leaves,
                         total_leaves=total_leaves,
                         approved=approved,
                         pending=pending,
                         rejected=rejected,
                         current_status=status,
                         current_leave_type=leave_type)


@reports.route('/loan-report')
@login_required
def loan_report():
    """Loan report"""
    if current_user.role not in ['admin', 'hr']:
        flash('Access denied.', 'error')
        return redirect(url_for('main.dashboard'))
    
    status = request.args.get('status', '')
    
    query = Loan.query
    if status:
        query = query.filter_by(status=status)
    
    loans = query.order_by(Loan.application_date.desc()).all()
    
    # Summary
    total_loans = len(loans)
    total_amount = sum(l.loan_amount for l in loans)
    total_remaining = sum(l.remaining_balance for l in loans)
    
    return render_template('reports/loan_report.html',
                         loans=loans,
                         total_loans=total_loans,
                         total_amount=total_amount,
                         total_remaining=total_remaining,
                         current_status=status)


@reports.route('/export/<report_type>')
@login_required
def export_report(report_type):
    """Export report to CSV"""
    if current_user.role not in ['admin', 'hr']:
        flash('Access denied.', 'error')
        return redirect(url_for('main.dashboard'))
    
    # Implementation for CSV export would go here
    # For now, just redirect back
    flash('Export functionality coming soon!', 'info')
    return redirect(url_for('reports.index'))
