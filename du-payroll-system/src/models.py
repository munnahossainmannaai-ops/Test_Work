from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'main.login'
login_manager.login_message = 'Please log in to access this page.'

class User(db.Model):
    """User model for authentication"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='employee')  # admin, hr, employee
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship with employee
    employee = db.relationship('Employee', backref='user', uselist=False, cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_id(self):
        return str(self.id)
    
    def __repr__(self):
        return f'<User {self.username}>'


class Employee(db.Model):
    """Employee model for Dhaka University staff"""
    __tablename__ = 'employees'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.String(20), unique=True, nullable=False)  # DU-EMP-XXXX
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    date_of_birth = db.Column(db.Date)
    joining_date = db.Column(db.Date, nullable=False)
    
    # Department and Position
    department = db.Column(db.String(100), nullable=False)
    designation = db.Column(db.String(100), nullable=False)
    employee_type = db.Column(db.String(50), nullable=False)  # Permanent, Contractual, Temporary, Visiting
    faculty = db.Column(db.String(100))  # For teaching staff
    
    # Salary Information
    basic_salary = db.Column(db.Float, nullable=False)
    house_rent_allowance = db.Column(db.Float, default=0.0)
    medical_allowance = db.Column(db.Float, default=0.0)
    transport_allowance = db.Column(db.Float, default=0.0)
    other_allowances = db.Column(db.Float, default=0.0)
    
    # Bank Information
    bank_name = db.Column(db.String(100))
    bank_account_number = db.Column(db.String(50))
    bank_branch = db.Column(db.String(100))
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    termination_date = db.Column(db.Date)
    
    # Relationships
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    payroll_records = db.relationship('Payroll', backref='employee', lazy='dynamic', cascade='all, delete-orphan')
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def gross_salary(self):
        return (self.basic_salary + self.house_rent_allowance + 
                self.medical_allowance + self.transport_allowance + 
                self.other_allowances)
    
    @property
    def total_deductions(self):
        return (self.basic_salary * 0.15) + (self.basic_salary * 0.10)  # Tax + Provident Fund
    
    @property
    def net_salary(self):
        return self.gross_salary - self.total_deductions
    
    def __repr__(self):
        return f'<Employee {self.employee_id} - {self.full_name}>'


class Payroll(db.Model):
    """Payroll records for each month"""
    __tablename__ = 'payroll'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    month = db.Column(db.Integer, nullable=False)  # 1-12
    year = db.Column(db.Integer, nullable=False)
    
    # Earnings
    basic_salary = db.Column(db.Float, nullable=False)
    house_rent_allowance = db.Column(db.Float, default=0.0)
    medical_allowance = db.Column(db.Float, default=0.0)
    transport_allowance = db.Column(db.Float, default=0.0)
    other_allowances = db.Column(db.Float, default=0.0)
    overtime_pay = db.Column(db.Float, default=0.0)
    bonus = db.Column(db.Float, default=0.0)
    
    # Deductions
    tax_deducted = db.Column(db.Float, default=0.0)
    provident_fund = db.Column(db.Float, default=0.0)
    gratuity = db.Column(db.Float, default=0.0)
    loan_deduction = db.Column(db.Float, default=0.0)
    other_deductions = db.Column(db.Float, default=0.0)
    
    # Totals
    gross_pay = db.Column(db.Float, nullable=False)
    total_deductions = db.Column(db.Float, nullable=False)
    net_pay = db.Column(db.Float, nullable=False)
    
    # Payment Status
    payment_status = db.Column(db.String(20), default='pending')  # pending, processed, paid
    payment_date = db.Column(db.Date)
    remarks = db.Column(db.Text)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    processed_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Unique constraint for employee per month/year
    __table_args__ = (db.UniqueConstraint('employee_id', 'month', 'year', name='unique_employee_month_year'),)
    
    @property
    def month_name(self):
        months = ['January', 'February', 'March', 'April', 'May', 'June',
                  'July', 'August', 'September', 'October', 'November', 'December']
        return months[self.month - 1]
    
    def calculate_totals(self):
        """Calculate gross pay, total deductions, and net pay"""
        self.gross_pay = (self.basic_salary + self.house_rent_allowance + 
                         self.medical_allowance + self.transport_allowance + 
                         self.other_allowances + self.overtime_pay + self.bonus)
        
        self.total_deductions = (self.tax_deducted + self.provident_fund + 
                                self.gratuity + self.loan_deduction + self.other_deductions)
        
        self.net_pay = self.gross_pay - self.total_deductions
    
    def __repr__(self):
        return f'<Payroll {self.employee_id} - {self.month_name} {self.year}>'


class Leave(db.Model):
    """Leave management for employees"""
    __tablename__ = 'leaves'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    leave_type = db.Column(db.String(50), nullable=False)  # Annual, Sick, Casual, Maternity, etc.
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    total_days = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    applied_date = db.Column(db.DateTime, default=datetime.utcnow)
    approved_date = db.Column(db.DateTime)
    
    def __repr__(self):
        return f'<Leave {self.employee_id} - {self.leave_type}>'


class Loan(db.Model):
    """Employee loan management"""
    __tablename__ = 'loans'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    loan_type = db.Column(db.String(50), nullable=False)  # House, Car, Personal, etc.
    loan_amount = db.Column(db.Float, nullable=False)
    interest_rate = db.Column(db.Float, default=0.0)
    tenure_months = db.Column(db.Integer, nullable=False)
    monthly_installment = db.Column(db.Float, nullable=False)
    remaining_balance = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='active')  # active, closed, rejected
    application_date = db.Column(db.DateTime, default=datetime.utcnow)
    approval_date = db.Column(db.DateTime)
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    def __repr__(self):
        return f'<Loan {self.employee_id} - {self.loan_type}>'


class AuditLog(db.Model):
    """Audit trail for tracking changes"""
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    action = db.Column(db.String(100), nullable=False)
    table_name = db.Column(db.String(50))
    record_id = db.Column(db.Integer)
    old_values = db.Column(db.Text)  # JSON string
    new_values = db.Column(db.Text)  # JSON string
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(45))
    
    def __repr__(self):
        return f'<AuditLog {self.action} at {self.timestamp}>'
