from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from src.models import db, Leave, Employee
from src.forms import LeaveForm
from datetime import datetime

leaves = Blueprint('leaves', __name__, url_prefix='/leaves')


@leaves.route('/')
@login_required
def list_leaves():
    """List all leave requests"""
    if current_user.role not in ['admin', 'hr']:
        # Employees can only see their own leaves
        leaves_query = Leave.query.filter_by(employee_id=current_user.employee.id)
    else:
        leaves_query = Leave.query
    
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')
    
    if status:
        leaves_query = leaves_query.filter_by(status=status)
    
    pagination = leaves_query.order_by(Leave.applied_date.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('leaves/list.html', 
                         leaves=pagination.items, 
                         pagination=pagination,
                         current_status=status)


@leaves.route('/apply', methods=['GET', 'POST'])
@login_required
def add_leave():
    """Apply for leave"""
    form = LeaveForm()
    
    if form.validate_on_submit():
        employee_id = current_user.employee.id if current_user.role == 'employee' else None
        
        # If admin/HR is applying on behalf of someone
        if current_user.role in ['admin', 'hr'] and request.form.get('employee_id'):
            employee_id = int(request.form.get('employee_id'))
        
        if not employee_id:
            flash('Employee information not found. Please complete your profile first.', 'error')
            return redirect(url_for('main.profile'))
        
        leave = Leave(
            employee_id=employee_id,
            leave_type=form.leave_type.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            total_days=form.total_days.data,
            reason=form.reason.data,
            status='pending' if current_user.role == 'employee' else 'approved'
        )
        
        if current_user.role in ['admin', 'hr']:
            leave.approved_by = current_user.id
            leave.approved_date = datetime.utcnow()
        
        db.session.add(leave)
        db.session.commit()
        
        flash('Leave application submitted successfully!', 'success')
        return redirect(url_for('leaves.list_leaves'))
    
    # If admin/HR, show employee selection
    employees = []
    if current_user.role in ['admin', 'hr']:
        employees = Employee.query.filter_by(is_active=True).order_by(Employee.full_name).all()
    
    return render_template('leaves/form.html', form=form, title='Apply for Leave', employees=employees)


@leaves.route('/<int:id>/approve', methods=['POST'])
@login_required
def approve_leave(id):
    """Approve leave request"""
    if current_user.role not in ['admin', 'hr']:
        flash('Access denied.', 'error')
        return redirect(url_for('main.dashboard'))
    
    leave = Leave.query.get_or_404(id)
    leave.status = 'approved'
    leave.approved_by = current_user.id
    leave.approved_date = datetime.utcnow()
    
    db.session.commit()
    flash('Leave request approved!', 'success')
    return redirect(url_for('leaves.list_leaves'))


@leaves.route('/<int:id>/reject', methods=['POST'])
@login_required
def reject_leave(id):
    """Reject leave request"""
    if current_user.role not in ['admin', 'hr']:
        flash('Access denied.', 'error')
        return redirect(url_for('main.dashboard'))
    
    leave = Leave.query.get_or_404(id)
    leave.status = 'rejected'
    leave.approved_by = current_user.id
    leave.approved_date = datetime.utcnow()
    
    db.session.commit()
    flash('Leave request rejected.', 'info')
    return redirect(url_for('leaves.list_leaves'))


@leaves.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete_leave(id):
    """Delete leave request"""
    leave = Leave.query.get_or_404(id)
    
    # Only allow deletion if pending or own leave
    if leave.status != 'pending' and current_user.role not in ['admin', 'hr']:
        flash('Cannot delete approved/rejected leaves.', 'error')
        return redirect(url_for('leaves.list_leaves'))
    
    db.session.delete(leave)
    db.session.commit()
    
    flash('Leave request deleted.', 'info')
    return redirect(url_for('leaves.list_leaves'))
