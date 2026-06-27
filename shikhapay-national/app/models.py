from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
import bcrypt

db = SQLAlchemy()

class User(UserMixin, db.Model):
    """User authentication model"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), default='Employee', nullable=False)  # Admin, HR, Employee, Accounts
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def check_password(self, password):
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))
    
    def __repr__(self):
        return f'<User {self.username}>'


class Employee(db.Model):
    """Employee information model"""
    __tablename__ = 'employees'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_code = db.Column(db.String(20), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    designation = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(100), nullable=False)
    basic_salary = db.Column(db.Float, default=0.0, nullable=False)
    joining_date = db.Column(db.Date, default=datetime.utcnow)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    bank_account = db.Column(db.String(50))
    bank_name = db.Column(db.String(100))
    address = db.Column(db.Text)
    nid_number = db.Column(db.String(20), unique=True)
    tin_number = db.Column(db.String(20))
    employment_type = db.Column(db.String(20), default='Permanent')  # Permanent, Contractual, Visiting
    status = db.Column(db.String(20), default='Active')  # Active, On Leave, Retired, Terminated
    
    # Relationships
    user = db.relationship('User', backref='employee', uselist=False)
    payrolls = db.relationship('Payroll', backref='employee', lazy='dynamic')
    loans = db.relationship('Loan', backref='employee', lazy='dynamic')
    attendance_records = db.relationship('Attendance', backref='employee', lazy='dynamic')
    leaves = db.relationship('LeaveApplication', backref='employee', lazy='dynamic')
    
    def get_monthly_gross(self):
        """Calculate gross salary with allowances"""
        house_rent = self.basic_salary * 0.60  # 60% of basic
        medical = self.basic_salary * 0.075   # 7.5% of basic
        transport = self.get_transport_allowance()
        other = self.basic_salary * 0.05       # 5% other allowances
        
        return self.basic_salary + house_rent + medical + transport + other
    
    def get_transport_allowance(self):
        """Get transport allowance based on designation"""
        transport_rates = {
            'Vice-Chancellor': 15000,
            'Pro-Vice-Chancellor': 12000,
            'Treasurer': 12000,
            'Professor': 10000,
            'Associate Professor': 8000,
            'Assistant Professor': 6000,
            'Lecturer': 4000,
            'Registrar': 10000,
            'Controller': 10000,
            'Director': 9000,
            'Deputy Registrar': 7000,
            'Assistant Registrar': 5000,
            'Accountant': 5000,
            'Office Assistant': 3000,
            'Security Guard': 2500,
            'Driver': 3500
        }
        return transport_rates.get(self.designation, 3000)
    
    def __repr__(self):
        return f'<Employee {self.name} ({self.employee_code})>'


class Payroll(db.Model):
    """Monthly payroll records"""
    __tablename__ = 'payrolls'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    month = db.Column(db.String(20), nullable=False, index=True)
    year = db.Column(db.Integer, nullable=False, index=True)
    
    # Earnings
    basic_salary = db.Column(db.Float, nullable=False)
    house_rent_allowance = db.Column(db.Float, default=0.0)
    medical_allowance = db.Column(db.Float, default=0.0)
    transport_allowance = db.Column(db.Float, default=0.0)
    other_allowances = db.Column(db.Float, default=0.0)
    festival_bonus = db.Column(db.Float, default=0.0)
    gross_salary = db.Column(db.Float, nullable=False)
    
    # Deductions
    tax_deduction = db.Column(db.Float, default=0.0)
    provident_fund = db.Column(db.Float, default=0.0)
    loan_deduction = db.Column(db.Float, default=0.0)
    absent_deduction = db.Column(db.Float, default=0.0)
    other_deductions = db.Column(db.Float, default=0.0)
    total_deductions = db.Column(db.Float, default=0.0)
    
    # Net salary
    net_salary = db.Column(db.Float, nullable=False)
    
    # Payment status
    payment_status = db.Column(db.String(20), default='Pending')  # Pending, Processing, Paid, Failed
    payment_date = db.Column(db.Date)
    bank_transaction_id = db.Column(db.String(100))
    
    # Metadata
    generated_at = db.Column(db.DateTime, default=datetime.utcnow)
    generated_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    payslip_pdf_path = db.Column(db.String(255))
    remarks = db.Column(db.Text)
    
    __table_args__ = (
        db.UniqueConstraint('employee.id', 'month', 'year', name='unique_employee_month_year'),
    )
    
    def __repr__(self):
        return f'<Payroll {self.employee_id} - {self.month}/{self.year}>'


class Loan(db.Model):
    """Employee loan management"""
    __tablename__ = 'loans'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    loan_type = db.Column(db.String(50), nullable=False)  # House Building, Car, Personal, Medical
    amount = db.Column(db.Float, nullable=False)
    balance = db.Column(db.Float, nullable=False)
    interest_rate = db.Column(db.Float, default=0.0)
    tenure_months = db.Column(db.Integer, nullable=False)
    monthly_installment = db.Column(db.Float, nullable=False)
    
    status = db.Column(db.String(20), default='Pending')  # Pending, Approved, Rejected, Disbursed, Closed
    application_date = db.Column(db.DateTime, default=datetime.utcnow)
    approval_date = db.Column(db.DateTime)
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    disbursal_date = db.Column(db.Date)
    closing_date = db.Column(db.Date)
    
    purpose = db.Column(db.Text)
    guarantor_info = db.Column(db.Text)
    
    def __repr__(self):
        return f'<Loan {self.loan_type} - {self.employee_id}>'


class Attendance(db.Model):
    """Daily attendance records"""
    __tablename__ = 'attendance'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    date = db.Column(db.Date, nullable=False, index=True)
    status = db.Column(db.String(20), nullable=False)  # Present, Absent, Leave, Holiday
    check_in = db.Column(db.Time)
    check_out = db.Column(db.Time)
    remarks = db.Column(db.Text)
    
    marked_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    marked_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('employee.id', 'date', name='unique_employee_date'),
    )
    
    def __repr__(self):
        return f'<Attendance {self.employee_id} - {self.date}>'


class LeaveApplication(db.Model):
    """Leave application and tracking"""
    __tablename__ = 'leave_applications'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    leave_type = db.Column(db.String(50), nullable=False)  # Casual, Sick, Earned, Maternity, Study
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    total_days = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.Text, nullable=False)
    
    status = db.Column(db.String(20), default='Pending')  # Pending, Approved, Rejected, Cancelled
    application_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    approval_date = db.Column(db.DateTime)
    rejection_reason = db.Column(db.Text)
    
    def __repr__(self):
        return f'<Leave {self.leave_type} - {self.employee_id}>'


class ResearchGrant(db.Model):
    """Research grant and project funding"""
    __tablename__ = 'research_grants'
    
    id = db.Column(db.Integer, primary_key=True)
    grant_code = db.Column(db.String(50), unique=True, nullable=False)
    title = db.Column(db.String(200), nullable=False)
    principal_investigator = db.Column(db.Integer, db.ForeignKey('employees.id'))
    co_investigators = db.Column(db.Text)  # JSON array of employee IDs
    
    funding_agency = db.Column(db.String(100), nullable=False)
    total_budget = db.Column(db.Float, nullable=False)
    allocated_budget = db.Column(db.Float, default=0.0)
    utilized_budget = db.Column(db.Float, default=0.0)
    
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default='Active')  # Active, Completed, Suspended, Terminated
    
    salary_charge_percentage = db.Column(db.Float, default=0.0)
    compliance_requirements = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Grant {self.grant_code} - {self.title}>'


class AuditLog(db.Model):
    """System audit trail for security and compliance"""
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    action = db.Column(db.String(100), nullable=False)
    entity_type = db.Column(db.String(50))  # Employee, Payroll, Loan, etc.
    entity_id = db.Column(db.Integer)
    old_values = db.Column(db.Text)  # JSON
    new_values = db.Column(db.Text)  # JSON
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(255))
    
    def __repr__(self):
        return f'<AuditLog {self.action} at {self.timestamp}>'
