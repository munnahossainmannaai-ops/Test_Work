from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from src.models import db, Loan, Employee
from src.forms import LoanForm
from datetime import datetime

loans = Blueprint('loans', __name__, url_prefix='/loans')


@loans.route('/')
@login_required
def list_loans():
    """List all loans"""
    if current_user.role not in ['admin', 'hr']:
        # Employees can only see their own loans
        loans_query = Loan.query.filter_by(employee_id=current_user.employee.id)
    else:
        loans_query = Loan.query
    
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')
    
    if status:
        loans_query = loans_query.filter_by(status=status)
    
    pagination = loans_query.order_by(Loan.application_date.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('loans/list.html', 
                         loans=pagination.items, 
                         pagination=pagination,
                         current_status=status)


@loans.route('/apply', methods=['GET', 'POST'])
@login_required
def apply_loan():
    """Apply for a loan"""
    form = LoanForm()
    
    if form.validate_on_submit():
        employee_id = current_user.employee.id if current_user.employee else None
        
        if not employee_id:
            flash('Employee information not found. Please complete your profile first.', 'error')
            return redirect(url_for('main.profile'))
        
        # Calculate monthly installment (simple calculation)
        monthly_installment = form.loan_amount.data / form.tenure_months.data
        
        loan = Loan(
            employee_id=employee_id,
            loan_type=form.loan_type.data,
            loan_amount=form.loan_amount.data,
            interest_rate=form.interest_rate.data or 0,
            tenure_months=form.tenure_months.data,
            monthly_installment=monthly_installment,
            remaining_balance=form.loan_amount.data,
            status='pending' if current_user.role == 'employee' else 'active'
        )
        
        if current_user.role in ['admin', 'hr']:
            loan.approved_by = current_user.id
            loan.approval_date = datetime.utcnow()
        
        db.session.add(loan)
        db.session.commit()
        
        flash('Loan application submitted successfully!', 'success')
        return redirect(url_for('loans.list_loans'))
    
    return render_template('loans/form.html', form=form, title='Apply for Loan')


@loans.route('/<int:id>/approve', methods=['POST'])
@login_required
def approve_loan(id):
    """Approve loan application"""
    if current_user.role not in ['admin', 'hr']:
        flash('Access denied.', 'error')
        return redirect(url_for('main.dashboard'))
    
    loan = Loan.query.get_or_404(id)
    loan.status = 'active'
    loan.approved_by = current_user.id
    loan.approval_date = datetime.utcnow()
    
    db.session.commit()
    flash('Loan approved!', 'success')
    return redirect(url_for('loans.list_loans'))


@loans.route('/<int:id>/reject', methods=['POST'])
@login_required
def reject_loan(id):
    """Reject loan application"""
    if current_user.role not in ['admin', 'hr']:
        flash('Access denied.', 'error')
        return redirect(url_for('main.dashboard'))
    
    loan = Loan.query.get_or_404(id)
    loan.status = 'rejected'
    
    db.session.commit()
    flash('Loan application rejected.', 'info')
    return redirect(url_for('loans.list_loans'))


@loans.route('/<int:id>/repay', methods=['POST'])
@login_required
def repay_loan(id):
    """Record loan repayment"""
    if current_user.role not in ['admin', 'hr']:
        flash('Access denied.', 'error')
        return redirect(url_for('main.dashboard'))
    
    loan = Loan.query.get_or_404(id)
    amount = float(request.form.get('amount', loan.monthly_installment))
    
    if amount > loan.remaining_balance:
        amount = loan.remaining_balance
    
    loan.remaining_balance -= amount
    
    if loan.remaining_balance <= 0:
        loan.remaining_balance = 0
        loan.status = 'closed'
    
    db.session.commit()
    flash(f'Repayment of ৳{amount:.2f} recorded. Remaining balance: ৳{loan.remaining_balance:.2f}', 'success')
    return redirect(url_for('loans.list_loans'))


@loans.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete_loan(id):
    """Delete loan"""
    if current_user.role not in ['admin', 'hr']:
        flash('Access denied.', 'error')
        return redirect(url_for('main.dashboard'))
    
    loan = Loan.query.get_or_404(id)
    db.session.delete(loan)
    db.session.commit()
    
    flash('Loan record deleted.', 'info')
    return redirect(url_for('loans.list_loans'))
