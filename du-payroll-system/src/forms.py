from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField, DateField, FloatField, TextAreaField, IntegerField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional, NumberRange
from datetime import date


class LoginForm(FlaskForm):
    """Login form"""
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=80)])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class RegistrationForm(FlaskForm):
    """User registration form"""
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=80)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    role = SelectField('Role', choices=[('employee', 'Employee'), ('hr', 'HR Manager'), ('admin', 'Administrator')], 
                      validators=[DataRequired()])
    submit = SubmitField('Register')


class EmployeeForm(FlaskForm):
    """Employee information form"""
    employee_id = StringField('Employee ID', validators=[DataRequired(), Length(max=20)])
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=50)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=50)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone', validators=[Optional(), Length(max=20)])
    date_of_birth = DateField('Date of Birth', format='%Y-%m-%d', validators=[Optional()])
    joining_date = DateField('Joining Date', format='%Y-%m-%d', validators=[DataRequired()])
    
    department = StringField('Department', validators=[DataRequired(), Length(max=100)])
    designation = StringField('Designation', validators=[DataRequired(), Length(max=100)])
    employee_type = SelectField('Employee Type', 
                               choices=[('Permanent', 'Permanent'), 
                                       ('Contractual', 'Contractual'), 
                                       ('Temporary', 'Temporary'), 
                                       ('Visiting', 'Visiting')],
                               validators=[DataRequired()])
    faculty = StringField('Faculty (if applicable)', validators=[Optional(), Length(max=100)])
    
    basic_salary = FloatField('Basic Salary', validators=[DataRequired(), NumberRange(min=0)])
    house_rent_allowance = FloatField('House Rent Allowance', validators=[Optional(), NumberRange(min=0)])
    medical_allowance = FloatField('Medical Allowance', validators=[Optional(), NumberRange(min=0)])
    transport_allowance = FloatField('Transport Allowance', validators=[Optional(), NumberRange(min=0)])
    other_allowances = FloatField('Other Allowances', validators=[Optional(), NumberRange(min=0)])
    
    bank_name = StringField('Bank Name', validators=[Optional(), Length(max=100)])
    bank_account_number = StringField('Bank Account Number', validators=[Optional(), Length(max=50)])
    bank_branch = StringField('Bank Branch', validators=[Optional(), Length(max=100)])
    
    is_active = BooleanField('Active')
    submit = SubmitField('Save Employee')


class PayrollForm(FlaskForm):
    """Payroll processing form"""
    employee_id = SelectField('Employee', coerce=int, validators=[DataRequired()])
    month = SelectField('Month', coerce=int, 
                       choices=[(1, 'January'), (2, 'February'), (3, 'March'), (4, 'April'),
                               (5, 'May'), (6, 'June'), (7, 'July'), (8, 'August'),
                               (9, 'September'), (10, 'October'), (11, 'November'), (12, 'December')],
                       validators=[DataRequired()])
    year = IntegerField('Year', validators=[DataRequired(), NumberRange(min=2000, max=2100)])
    
    basic_salary = FloatField('Basic Salary', validators=[DataRequired(), NumberRange(min=0)])
    house_rent_allowance = FloatField('House Rent Allowance', validators=[Optional(), NumberRange(min=0)])
    medical_allowance = FloatField('Medical Allowance', validators=[Optional(), NumberRange(min=0)])
    transport_allowance = FloatField('Transport Allowance', validators=[Optional(), NumberRange(min=0)])
    other_allowances = FloatField('Other Allowances', validators=[Optional(), NumberRange(min=0)])
    overtime_pay = FloatField('Overtime Pay', validators=[Optional(), NumberRange(min=0)])
    bonus = FloatField('Bonus', validators=[Optional(), NumberRange(min=0)])
    
    tax_deducted = FloatField('Tax Deducted', validators=[Optional(), NumberRange(min=0)])
    provident_fund = FloatField('Provident Fund', validators=[Optional(), NumberRange(min=0)])
    gratuity = FloatField('Gratuity', validators=[Optional(), NumberRange(min=0)])
    loan_deduction = FloatField('Loan Deduction', validators=[Optional(), NumberRange(min=0)])
    other_deductions = FloatField('Other Deductions', validators=[Optional(), NumberRange(min=0)])
    
    payment_status = SelectField('Payment Status', 
                                choices=[('pending', 'Pending'), ('processed', 'Processed'), ('paid', 'Paid')],
                                validators=[DataRequired()])
    payment_date = DateField('Payment Date', format='%Y-%m-%d', validators=[Optional()])
    remarks = TextAreaField('Remarks', validators=[Optional()])
    
    submit = SubmitField('Process Payroll')


class LeaveForm(FlaskForm):
    """Leave application form"""
    leave_type = SelectField('Leave Type', 
                            choices=[('Annual', 'Annual Leave'), 
                                    ('Sick', 'Sick Leave'), 
                                    ('Casual', 'Casual Leave'), 
                                    ('Maternity', 'Maternity Leave'),
                                    ('Paternity', 'Paternity Leave'),
                                    ('Study', 'Study Leave'),
                                    ('Unpaid', 'Unpaid Leave')],
                            validators=[DataRequired()])
    start_date = DateField('Start Date', format='%Y-%m-%d', validators=[DataRequired()])
    end_date = DateField('End Date', format='%Y-%m-%d', validators=[DataRequired()])
    total_days = IntegerField('Total Days', validators=[DataRequired(), NumberRange(min=1)])
    reason = TextAreaField('Reason', validators=[DataRequired()])
    submit = SubmitField('Apply for Leave')


class LoanForm(FlaskForm):
    """Loan application form"""
    loan_type = SelectField('Loan Type', 
                           choices=[('House', 'House Loan'), 
                                   ('Car', 'Car Loan'), 
                                   ('Personal', 'Personal Loan'), 
                                   ('Education', 'Education Loan')],
                           validators=[DataRequired()])
    loan_amount = FloatField('Loan Amount', validators=[DataRequired(), NumberRange(min=1000)])
    interest_rate = FloatField('Interest Rate (%)', validators=[Optional(), NumberRange(min=0, max=100)])
    tenure_months = IntegerField('Tenure (Months)', validators=[DataRequired(), NumberRange(min=1, max=360)])
    submit = SubmitField('Apply for Loan')
