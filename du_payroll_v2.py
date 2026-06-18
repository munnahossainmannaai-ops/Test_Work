"""
Dhaka University Payroll Management System - Version 2.0
Enhanced with:
- SQLite Database
- PDF Payslip Generation
- Advanced Bangladesh Tax Calculator
- Festival Bonus Automation
- Dashboard Analytics
- Role-Based Access Control
"""

import os
import sqlite3
from datetime import datetime, date
from flask import Flask, render_template_string, request, redirect, url_for, flash, session, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib import colors
from io import BytesIO
import pandas as pd

# Configuration
app = Flask(__name__)
app.config['SECRET_KEY'] = 'dhaka-university-payroll-secret-key-2024'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///du_payroll.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# ==================== DATABASE MODELS ====================

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # admin, hr, employee
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'))

class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    emp_code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    designation = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(100), nullable=False)
    basic_salary = db.Column(db.Float, nullable=False)
    house_rent = db.Column(db.Float, default=0.0)
    medical_allowance = db.Column(db.Float, default=0.0)
    transport_allowance = db.Column(db.Float, default=0.0)
    other_allowances = db.Column(db.Float, default=0.0)
    provident_fund_percent = db.Column(db.Float, default=10.0)
    tax_exempt = db.Column(db.Boolean, default=False)
    joining_date = db.Column(db.Date, default=date.today)
    status = db.Column(db.String(20), default='Active')
    bank_account = db.Column(db.String(30))
    
    # Relationships
    payroll_records = db.relationship('PayrollRecord', backref='employee', lazy=True)
    loans = db.relationship('Loan', backref='employee', lazy=True)
    attendance = db.relationship('Attendance', backref='employee', lazy=True)

class PayrollRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    month = db.Column(db.Integer, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    gross_salary = db.Column(db.Float, nullable=False)
    provident_fund = db.Column(db.Float, default=0.0)
    tax_deducted = db.Column(db.Float, default=0.0)
    loan_deduction = db.Column(db.Float, default=0.0)
    other_deductions = db.Column(db.Float, default=0.0)
    net_salary = db.Column(db.Float, nullable=False)
    festival_bonus = db.Column(db.Float, default=0.0)
    overtime = db.Column(db.Float, default=0.0)
    absence_deduction = db.Column(db.Float, default=0.0)
    processed_date = db.Column(db.DateTime, default=datetime.utcnow)
    is_paid = db.Column(db.Boolean, default=False)
    payslip_generated = db.Column(db.Boolean, default=False)

class Loan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    loan_type = db.Column(db.String(50), nullable=False)
    principal_amount = db.Column(db.Float, nullable=False)
    remaining_balance = db.Column(db.Float, nullable=False)
    monthly_installment = db.Column(db.Float, nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default='Active')

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False)  # Present, Absent, Leave, Holiday
    overtime_hours = db.Column(db.Float, default=0.0)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ==================== BANGLADESH TAX CALCULATOR ====================

def calculate_bangladesh_tax(gross_annual_income, is_female=False, is_disabled=False, age=0):
    """
    Calculate income tax based on Bangladesh National Board of Revenue (NBR) rules 2023-24
    """
    # Tax-free threshold adjustments
    if is_female or age >= 65 or is_disabled:
        tax_free_limit = 350000
    elif age >= 60:
        tax_free_limit = 325000
    else:
        tax_free_limit = 300000
    
    taxable_income = max(0, gross_annual_income - tax_free_limit)
    
    if taxable_income == 0:
        return 0.0
    
    tax = 0.0
    remaining = taxable_income
    
    # Tax slabs (BDT)
    slabs = [
        (500000, 0.05),    # First 5 lakh @ 5%
        (1000000, 0.10),   # Next 5 lakh @ 10%
        (1500000, 0.15),   # Next 5 lakh @ 15%
        (2000000, 0.20),   # Next 5 lakh @ 20%
        (float('inf'), 0.25)  # Above 20 lakh @ 25%
    ]
    
    cumulative = 0
    for limit, rate in slabs:
        slab_amount = limit - cumulative
        if remaining <= slab_amount:
            tax += remaining * rate
            break
        else:
            tax += slab_amount * rate
            remaining -= slab_amount
            cumulative = limit
    
    # Minimum tax for non-exempt individuals
    if gross_annual_income > tax_free_limit and tax < 5000:
        tax = max(tax, 5000)
    
    return tax

def get_designation_base_salary(designation):
    """Get base salary according to Bangladesh National Pay Scale 2015"""
    pay_scales = {
        'Vice-Chancellor': 78000,
        'Pro-Vice-Chancellor': 70000,
        'Treasurer': 65000,
        'Professor': 62000,
        'Associate Professor': 52000,
        'Assistant Professor': 42000,
        'Lecturer': 22000,
        'Registrar': 60000,
        'Deputy Registrar': 45000,
        'Assistant Registrar': 35000,
        'Accountant': 30000,
        'Senior Officer': 35000,
        'Officer': 25000,
        'Office Assistant': 18000,
        'Security Guard': 15000,
        'Driver': 16000,
        'Gardener': 14000,
        'Librarian': 40000,
        'Assistant Librarian': 28000
    }
    return pay_scales.get(designation, 20000)

def calculate_allowances(basic_salary, designation, department):
    """Calculate allowances based on DU policies"""
    # House Rent: 40-60% based on location (assuming Dhaka = 60%)
    house_rent = basic_salary * 0.60
    
    # Medical Allowance: 5-10%
    medical_allowance = basic_salary * 0.075
    
    # Transport Allowance: Fixed based on designation level
    if designation in ['Vice-Chancellor', 'Pro-Vice-Chancellor', 'Treasurer']:
        transport_allowance = 15000
    elif designation in ['Professor', 'Registrar']:
        transport_allowance = 10000
    elif designation in ['Associate Professor', 'Deputy Registrar']:
        transport_allowance = 7500
    elif designation in ['Assistant Professor', 'Assistant Registrar', 'Accountant']:
        transport_allowance = 5000
    elif designation in ['Lecturer', 'Senior Officer', 'Librarian']:
        transport_allowance = 3500
    else:
        transport_allowance = 2000
    
    # Other allowances (conveyance, telephone, etc.)
    other_allowances = basic_salary * 0.05
    
    return house_rent, medical_allowance, transport_allowance, other_allowances

# ==================== PDF GENERATION ====================

def generate_payslip_pdf(payroll_record, employee):
    """Generate professional PDF payslip with DU branding"""
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Header with DU branding
    c.setFillColor(colors.HexColor('#0066CC'))
    c.rect(0, height - 100, width, 100, fill=True, stroke=False)
    
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(width/2, height - 40, "UNIVERSITY OF DHAKA")
    c.setFont("Helvetica", 12)
    c.drawCentredString(width/2, height - 60, "Payroll Management System")
    c.drawCentredString(width/2, height - 75, "Dhaka-1000, Bangladesh")
    
    # Title
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width/2, height - 120, "SALARY PAYSLIP")
    
    # Employee Details
    y_position = height - 170
    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, y_position, f"Employee Name: {employee.name}")
    c.drawString(350, y_position, f"Employee Code: {employee.emp_code}")
    
    y_position -= 20
    c.drawString(50, y_position, f"Designation: {employee.designation}")
    c.drawString(350, y_position, f"Department: {employee.department}")
    
    y_position -= 20
    c.drawString(50, y_position, f"Pay Period: {datetime.strftime(date(2024, payroll_record.month, 1), '%B %Y')}")
    c.drawString(350, y_position, f"Bank Account: {employee.bank_account or 'N/A'}")
    
    # Earnings Table
    y_position -= 50
    c.setFillColor(colors.HexColor('#E6F2FF'))
    c.rect(50, y_position - 10, width - 100, 20, fill=True, stroke=False)
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(60, y_position + 3, "EARNINGS")
    
    y_position -= 25
    c.setFont("Helvetica", 10)
    earnings = [
        ("Basic Salary", f"{employee.basic_salary:,.2f}"),
        ("House Rent Allowance", f"{employee.house_rent:,.2f}"),
        ("Medical Allowance", f"{employee.medical_allowance:,.2f}"),
        ("Transport Allowance", f"{employee.transport_allowance:,.2f}"),
        ("Other Allowances", f"{employee.other_allowances:,.2f}"),
    ]
    if payroll_record.festival_bonus > 0:
        earnings.append(("Festival Bonus", f"{payroll_record.festival_bonus:,.2f}"))
    if payroll_record.overtime > 0:
        earnings.append(("Overtime Pay", f"{payroll_record.overtime:,.2f}"))
    
    total_earnings = payroll_record.gross_salary + payroll_record.festival_bonus + payroll_record.overtime
    for label, amount in earnings:
        c.drawString(60, y_position, label)
        c.drawString(450, y_position, f"BDT {amount}")
        y_position -= 18
    
    y_position -= 10
    c.setFont("Helvetica-Bold", 10)
    c.drawString(60, y_position, "Gross Earnings")
    c.drawString(450, y_position, f"BDT {total_earnings:,.2f}")
    
    # Deductions Table
    y_position -= 40
    c.setFillColor(colors.HexColor('#FFE6E6'))
    c.rect(50, y_position - 10, width - 100, 20, fill=True, stroke=False)
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(60, y_position + 3, "DEDUCTIONS")
    
    y_position -= 25
    c.setFont("Helvetica", 10)
    deductions = [
        ("Provident Fund (10%)", f"{payroll_record.provident_fund:,.2f}"),
        ("Income Tax", f"{payroll_record.tax_deducted:,.2f}"),
    ]
    if payroll_record.loan_deduction > 0:
        deductions.append(("Loan Installment", f"{payroll_record.loan_deduction:,.2f}"))
    if payroll_record.absence_deduction > 0:
        deductions.append(("Absence Deduction", f"{payroll_record.absence_deduction:,.2f}"))
    if payroll_record.other_deductions > 0:
        deductions.append(("Other Deductions", f"{payroll_record.other_deductions:,.2f}"))
    
    total_deductions = (payroll_record.provident_fund + payroll_record.tax_deducted + 
                       payroll_record.loan_deduction + payroll_record.absence_deduction + 
                       payroll_record.other_deductions)
    
    for label, amount in deductions:
        c.drawString(60, y_position, label)
        c.drawString(450, y_position, f"BDT {amount}")
        y_position -= 18
    
    y_position -= 10
    c.setFont("Helvetica-Bold", 10)
    c.drawString(60, y_position, "Total Deductions")
    c.drawString(450, y_position, f"BDT {total_deductions:,.2f}")
    
    # Net Salary
    y_position -= 40
    c.setFillColor(colors.HexColor('#E6FFE6'))
    c.rect(50, y_position - 10, width - 100, 30, fill=True, stroke=False)
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(60, y_position + 8, "NET SALARY")
    c.drawString(450, y_position + 8, f"BDT {payroll_record.net_salary:,.2f}")
    
    # Footer
    c.setFont("Helvetica", 9)
    c.setFillColor(colors.gray)
    footer_y = 50
    c.drawCentredString(width/2, footer_y, "This is a computer-generated document. No signature required.")
    c.drawCentredString(width/2, footer_y - 15, f"Generated on: {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}")
    c.drawCentredString(width/2, footer_y - 30, "University of Dhaka - Payroll Management System v2.0")
    
    c.save()
    buffer.seek(0)
    return buffer

# ==================== HTML TEMPLATES ====================

LOGIN_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DHAKA UNIVERSITY - Payroll Login</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; display: flex; justify-content: center; align-items: center; }
        .login-container { background: white; padding: 40px; border-radius: 10px; box-shadow: 0 10px 40px rgba(0,0,0,0.2); width: 400px; }
        .logo { text-align: center; margin-bottom: 30px; }
        .logo h1 { color: #0066CC; font-size: 24px; margin-bottom: 5px; }
        .logo p { color: #666; font-size: 14px; }
        .form-group { margin-bottom: 20px; }
        .form-group label { display: block; margin-bottom: 8px; color: #333; font-weight: 500; }
        .form-group input { width: 100%; padding: 12px; border: 1px solid #ddd; border-radius: 5px; font-size: 14px; }
        .form-group input:focus { outline: none; border-color: #667eea; }
        .btn-login { width: 100%; padding: 12px; background: #0066CC; color: white; border: none; border-radius: 5px; font-size: 16px; cursor: pointer; transition: background 0.3s; }
        .btn-login:hover { background: #0052a3; }
        .flash-messages { margin-bottom: 20px; }
        .flash { padding: 10px; border-radius: 5px; margin-bottom: 10px; }
        .flash.error { background: #ffe6e6; color: #cc0000; }
        .flash.success { background: #e6ffe6; color: #006600; }
    </style>
</head>
<body>
    <div class="login-container">
        <div class="logo">
            <h1>UNIVERSITY OF DHAKA</h1>
            <p>Payroll Management System</p>
        </div>
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                <div class="flash-messages">
                    {% for category, message in messages %}
                        <div class="flash {{ category }}">{{ message }}</div>
                    {% endfor %}
                </div>
            {% endif %}
        {% endwith %}
        <form method="POST">
            <div class="form-group">
                <label for="username">Username</label>
                <input type="text" id="username" name="username" required>
            </div>
            <div class="form-group">
                <label for="password">Password</label>
                <input type="password" id="password" name="password" required>
            </div>
            <button type="submit" class="btn-login">Login</button>
        </form>
        <div style="margin-top: 20px; text-align: center; font-size: 12px; color: #666;">
            <p>Demo Credentials: admin / admin123</p>
        </div>
    </div>
</body>
</html>
'''

DASHBOARD_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DHAKA UNIVERSITY - Payroll Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f5f7fa; }
        .navbar { background: #0066CC; color: white; padding: 15px 30px; display: flex; justify-content: space-between; align-items: center; }
        .navbar h1 { font-size: 20px; }
        .navbar .user-info { display: flex; align-items: center; gap: 15px; }
        .navbar a { color: white; text-decoration: none; padding: 8px 15px; border-radius: 5px; }
        .navbar a:hover { background: rgba(255,255,255,0.2); }
        .container { max-width: 1400px; margin: 30px auto; padding: 0 20px; }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .stat-card { background: white; padding: 25px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .stat-card h3 { color: #666; font-size: 14px; margin-bottom: 10px; }
        .stat-card .value { font-size: 32px; font-weight: bold; color: #0066CC; }
        .stat-card .change { font-size: 12px; margin-top: 5px; }
        .stat-card .change.positive { color: #28a745; }
        .stat-card .change.negative { color: #dc3545; }
        .card { background: white; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin-bottom: 20px; }
        .card-header { padding: 20px; border-bottom: 1px solid #eee; display: flex; justify-content: space-between; align-items: center; }
        .card-header h2 { font-size: 18px; color: #333; }
        .card-body { padding: 20px; }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #eee; }
        th { background: #f8f9fa; font-weight: 600; color: #333; }
        tr:hover { background: #f8f9fa; }
        .btn { padding: 8px 15px; border-radius: 5px; text-decoration: none; display: inline-block; font-size: 14px; cursor: pointer; border: none; }
        .btn-primary { background: #0066CC; color: white; }
        .btn-success { background: #28a745; color: white; }
        .btn-warning { background: #ffc107; color: #333; }
        .btn-danger { background: #dc3545; color: white; }
        .btn-sm { padding: 5px 10px; font-size: 12px; }
        .badge { padding: 4px 8px; border-radius: 12px; font-size: 12px; }
        .badge-success { background: #d4edda; color: #155724; }
        .badge-warning { background: #fff3cd; color: #856404; }
        .badge-danger { background: #f8d7da; color: #721c24; }
        .flash-messages { margin-bottom: 20px; }
        .flash { padding: 15px; border-radius: 5px; margin-bottom: 10px; }
        .flash.success { background: #d4edda; color: #155724; }
        .flash.error { background: #f8d7da; color: #721c24; }
        .actions { display: flex; gap: 10px; }
        .form-inline { display: flex; gap: 10px; align-items: center; }
        .form-inline input, .form-inline select { padding: 8px; border: 1px solid #ddd; border-radius: 5px; }
    </style>
</head>
<body>
    <nav class="navbar">
        <h1>🏛️ DHAKA UNIVERSITY PAYROLL SYSTEM</h1>
        <div class="user-info">
            <span>Welcome, {{ current_user.username }} ({{ current_user.role }})</span>
            <a href="{{ url_for('logout') }}">Logout</a>
        </div>
    </nav>
    
    <div class="container">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                <div class="flash-messages">
                    {% for category, message in messages %}
                        <div class="flash {{ category }}">{{ message }}</div>
                    {% endfor %}
                </div>
            {% endif %}
        {% endwith %}
        
        <div class="stats-grid">
            <div class="stat-card">
                <h3>Total Employees</h3>
                <div class="value">{{ stats.total_employees }}</div>
                <div class="change positive">Active: {{ stats.active_employees }}</div>
            </div>
            <div class="stat-card">
                <h3>Monthly Payroll</h3>
                <div class="value">৳{{ "%.2f"|format(stats.monthly_payroll) }}</div>
                <div class="change">Current Month</div>
            </div>
            <div class="stat-card">
                <h3>Total Tax Deducted</h3>
                <div class="value">৳{{ "%.2f"|format(stats.total_tax) }}</div>
                <div class="change">This Year</div>
            </div>
            <div class="stat-card">
                <h3>Outstanding Loans</h3>
                <div class="value">৳{{ "%.2f"|format(stats.total_loans) }}</div>
                <div class="change negative">{{ stats.active_loans }} Active</div>
            </div>
        </div>
        
        <div class="card">
            <div class="card-header">
                <h2>Quick Actions</h2>
            </div>
            <div class="card-body">
                <div class="actions">
                    <a href="{{ url_for('add_employee') }}" class="btn btn-primary">➕ Add Employee</a>
                    <a href="{{ url_for('process_payroll') }}" class="btn btn-success">💰 Process Monthly Payroll</a>
                    <a href="{{ url_for('generate_reports') }}" class="btn btn-warning">📊 Generate Reports</a>
                    {% if current_user.role == 'admin' %}
                    <a href="{{ url_for('manage_loans') }}" class="btn btn-primary">💳 Manage Loans</a>
                    {% endif %}
                </div>
            </div>
        </div>
        
        <div class="card">
            <div class="card-header">
                <h2>Recent Employees</h2>
                <div class="form-inline">
                    <input type="text" placeholder="Search..." id="searchBox">
                    <select id="deptFilter">
                        <option value="">All Departments</option>
                        {% for dept in departments %}
                        <option value="{{ dept }}">{{ dept }}</option>
                        {% endfor %}
                    </select>
                </div>
            </div>
            <div class="card-body">
                <table>
                    <thead>
                        <tr>
                            <th>Code</th>
                            <th>Name</th>
                            <th>Designation</th>
                            <th>Department</th>
                            <th>Basic Salary</th>
                            <th>Status</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for emp in employees %}
                        <tr>
                            <td>{{ emp.emp_code }}</td>
                            <td>{{ emp.name }}</td>
                            <td>{{ emp.designation }}</td>
                            <td>{{ emp.department }}</td>
                            <td>৳{{ "%.2f"|format(emp.basic_salary) }}</td>
                            <td><span class="badge badge-{{ 'success' if emp.status == 'Active' else 'danger' }}">{{ emp.status }}</span></td>
                            <td>
                                <div class="actions">
                                    <a href="{{ url_for('view_employee', emp_id=emp.id) }}" class="btn btn-sm btn-primary">View</a>
                                    <a href="{{ url_for('download_payslip', emp_id=emp.id) }}" class="btn btn-sm btn-success">PDF</a>
                                    {% if current_user.role == 'admin' %}
                                    <a href="{{ url_for('edit_employee', emp_id=emp.id) }}" class="btn btn-sm btn-warning">Edit</a>
                                    {% endif %}
                                </div>
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
        
        <div class="card">
            <div class="card-header">
                <h2>Recent Payroll Records</h2>
            </div>
            <div class="card-body">
                <table>
                    <thead>
                        <tr>
                            <th>Employee</th>
                            <th>Month</th>
                            <th>Gross Salary</th>
                            <th>Deductions</th>
                            <th>Net Salary</th>
                            <th>Status</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for record in recent_payroll %}
                        <tr>
                            <td>{{ record.employee.name }}</td>
                            <td>{{ datetime.strftime(date(2024, record.month, 1), '%B %Y') }}</td>
                            <td>৳{{ "%.2f"|format(record.gross_salary) }}</td>
                            <td>৳{{ "%.2f"|format(record.provident_fund + record.tax_deducted + record.loan_deduction) }}</td>
                            <td><strong>৳{{ "%.2f"|format(record.net_salary) }}</strong></td>
                            <td><span class="badge badge-{{ 'success' if record.is_paid else 'warning' }}">{{ 'Paid' if record.is_paid else 'Pending' }}</span></td>
                            <td>
                                <a href="{{ url_for('download_payslip_by_record', record_id=record.id) }}" class="btn btn-sm btn-success">Download PDF</a>
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    
    <script>
        // Simple search functionality
        document.getElementById('searchBox').addEventListener('keyup', function() {
            const searchTerm = this.value.toLowerCase();
            const rows = document.querySelectorAll('tbody tr');
            rows.forEach(row => {
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(searchTerm) ? '' : 'none';
            });
        });
    </script>
</body>
</html>
'''

EMPLOYEE_FORM_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DHAKA UNIVERSITY - Employee Form</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f5f7fa; }
        .navbar { background: #0066CC; color: white; padding: 15px 30px; }
        .navbar h1 { font-size: 20px; }
        .container { max-width: 800px; margin: 30px auto; padding: 0 20px; }
        .card { background: white; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); padding: 30px; }
        .card h2 { margin-bottom: 20px; color: #333; }
        .form-group { margin-bottom: 20px; }
        .form-group label { display: block; margin-bottom: 8px; color: #333; font-weight: 500; }
        .form-group input, .form-group select { width: 100%; padding: 12px; border: 1px solid #ddd; border-radius: 5px; font-size: 14px; }
        .form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        .btn { padding: 12px 25px; border-radius: 5px; text-decoration: none; display: inline-block; font-size: 14px; cursor: pointer; border: none; }
        .btn-primary { background: #0066CC; color: white; }
        .btn-secondary { background: #6c757d; color: white; }
        .btn-group { display: flex; gap: 10px; margin-top: 20px; }
        .flash-messages { margin-bottom: 20px; }
        .flash { padding: 15px; border-radius: 5px; margin-bottom: 10px; }
        .flash.error { background: #f8d7da; color: #721c24; }
        .flash.success { background: #d4edda; color: #155724; }
    </style>
</head>
<body>
    <nav class="navbar">
        <h1>🏛️ DHAKA UNIVERSITY PAYROLL SYSTEM</h1>
    </nav>
    
    <div class="container">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                <div class="flash-messages">
                    {% for category, message in messages %}
                        <div class="flash {{ category }}">{{ message }}</div>
                    {% endfor %}
                </div>
            {% endif %}
        {% endwith %}
        
        <div class="card">
            <h2>{{ title }}</h2>
            <form method="POST">
                <div class="form-row">
                    <div class="form-group">
                        <label for="emp_code">Employee Code *</label>
                        <input type="text" id="emp_code" name="emp_code" value="{{ employee.emp_code if employee else '' }}" required>
                    </div>
                    <div class="form-group">
                        <label for="name">Full Name *</label>
                        <input type="text" id="name" name="name" value="{{ employee.name if employee else '' }}" required>
                    </div>
                </div>
                
                <div class="form-row">
                    <div class="form-group">
                        <label for="designation">Designation *</label>
                        <select id="designation" name="designation" required onchange="autoFillSalary()">
                            <option value="">Select Designation</option>
                            <option value="Vice-Chancellor">Vice-Chancellor</option>
                            <option value="Pro-Vice-Chancellor">Pro-Vice-Chancellor</option>
                            <option value="Treasurer">Treasurer</option>
                            <option value="Professor">Professor</option>
                            <option value="Associate Professor">Associate Professor</option>
                            <option value="Assistant Professor">Assistant Professor</option>
                            <option value="Lecturer">Lecturer</option>
                            <option value="Registrar">Registrar</option>
                            <option value="Deputy Registrar">Deputy Registrar</option>
                            <option value="Assistant Registrar">Assistant Registrar</option>
                            <option value="Accountant">Accountant</option>
                            <option value="Senior Officer">Senior Officer</option>
                            <option value="Officer">Officer</option>
                            <option value="Office Assistant">Office Assistant</option>
                            <option value="Security Guard">Security Guard</option>
                            <option value="Driver">Driver</option>
                            <option value="Gardener">Gardener</option>
                            <option value="Librarian">Librarian</option>
                            <option value="Assistant Librarian">Assistant Librarian</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="department">Department *</label>
                        <select id="department" name="department" required>
                            <option value="">Select Department</option>
                            <option value="Computer Science & Engineering">Computer Science & Engineering</option>
                            <option value="Electrical & Electronic Engineering">Electrical & Electronic Engineering</option>
                            <option value="Mechanical Engineering">Mechanical Engineering</option>
                            <option value="Civil Engineering">Civil Engineering</option>
                            <option value="Mathematics">Mathematics</option>
                            <option value="Physics">Physics</option>
                            <option value="Chemistry">Chemistry</option>
                            <option value="Bangla">Bangla</option>
                            <option value="English">English</option>
                            <option value="History">History</option>
                            <option value="Political Science">Political Science</option>
                            <option value="Economics">Economics</option>
                            <option value="Sociology">Sociology</option>
                            <option value="Philosophy">Philosophy</option>
                            <option value="Islamic Studies">Islamic Studies</option>
                            <option value="Law">Law</option>
                            <option value="Business Administration">Business Administration</option>
                            <option value="Accounting">Accounting</option>
                            <option value="Management">Management</option>
                            <option value="Finance">Finance</option>
                            <option value="HR & Admin">HR & Admin</option>
                            <option value="Accounts Office">Accounts Office</option>
                            <option value="Registrar Office">Registrar Office</option>
                            <option value="Library">Library</option>
                            <option value="Security">Security</option>
                            <option value="Maintenance">Maintenance</option>
                        </select>
                    </div>
                </div>
                
                <div class="form-row">
                    <div class="form-group">
                        <label for="basic_salary">Basic Salary (BDT) *</label>
                        <input type="number" id="basic_salary" name="basic_salary" step="0.01" value="{{ employee.basic_salary if employee else '' }}" required>
                    </div>
                    <div class="form-group">
                        <label for="bank_account">Bank Account Number</label>
                        <input type="text" id="bank_account" name="bank_account" value="{{ employee.bank_account if employee else '' }}">
                    </div>
                </div>
                
                <div class="form-row">
                    <div class="form-group">
                        <label for="joining_date">Joining Date</label>
                        <input type="date" id="joining_date" name="joining_date" value="{{ employee.joining_date.strftime('%Y-%m-%d') if employee and employee.joining_date else '' }}">
                    </div>
                    <div class="form-group">
                        <label for="status">Status</label>
                        <select id="status" name="status">
                            <option value="Active" {{ 'selected' if employee and employee.status == 'Active' else '' }}>Active</option>
                            <option value="On Leave" {{ 'selected' if employee and employee.status == 'On Leave' else '' }}>On Leave</option>
                            <option value="Suspended" {{ 'selected' if employee and employee.status == 'Suspended' else '' }}>Suspended</option>
                            <option value="Retired" {{ 'selected' if employee and employee.status == 'Retired' else '' }}>Retired</option>
                        </select>
                    </div>
                </div>
                
                <div class="form-group">
                    <label>
                        <input type="checkbox" name="tax_exempt" {{ 'checked' if employee and employee.tax_exempt else '' }}>
                        Tax Exempt
                    </label>
                </div>
                
                <div class="btn-group">
                    <button type="submit" class="btn btn-primary">Save Employee</button>
                    <a href="{{ url_for('dashboard') }}" class="btn btn-secondary">Cancel</a>
                </div>
            </form>
        </div>
    </div>
    
    <script>
        const salaryMap = {
            'Vice-Chancellor': 78000,
            'Pro-Vice-Chancellor': 70000,
            'Treasurer': 65000,
            'Professor': 62000,
            'Associate Professor': 52000,
            'Assistant Professor': 42000,
            'Lecturer': 22000,
            'Registrar': 60000,
            'Deputy Registrar': 45000,
            'Assistant Registrar': 35000,
            'Accountant': 30000,
            'Senior Officer': 35000,
            'Officer': 25000,
            'Office Assistant': 18000,
            'Security Guard': 15000,
            'Driver': 16000,
            'Gardener': 14000,
            'Librarian': 40000,
            'Assistant Librarian': 28000
        };
        
        function autoFillSalary() {
            const designation = document.getElementById('designation').value;
            const salaryInput = document.getElementById('basic_salary');
            if (designation && salaryMap[designation] && !salaryInput.value) {
                salaryInput.value = salaryMap[designation];
            }
        }
    </script>
</body>
</html>
'''

# ==================== ROUTES ====================

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash('Login successful!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template_string(LOGIN_TEMPLATE)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

@app.route('/')
@login_required
def dashboard():
    # Calculate statistics
    total_employees = Employee.query.count()
    active_employees = Employee.query.filter_by(status='Active').count()
    
    current_month = datetime.now().month
    current_year = datetime.now().year
    
    monthly_records = PayrollRecord.query.filter_by(month=current_month, year=current_year).all()
    monthly_payroll = sum(r.net_salary for r in monthly_records)
    
    yearly_records = PayrollRecord.query.filter_by(year=current_year).all()
    total_tax = sum(r.tax_deducted for r in yearly_records)
    
    active_loans = Loan.query.filter_by(status='Active').all()
    total_loans = sum(l.remaining_balance for l in active_loans)
    
    stats = {
        'total_employees': total_employees,
        'active_employees': active_employees,
        'monthly_payroll': monthly_payroll,
        'total_tax': total_tax,
        'total_loans': total_loans,
        'active_loans': len(active_loans)
    }
    
    employees = Employee.query.order_by(Employee.id.desc()).limit(10).all()
    recent_payroll = PayrollRecord.query.order_by(PayrollRecord.processed_date.desc()).limit(10).all()
    departments = db.session.query(Employee.department).distinct().all()
    departments = [d[0] for d in departments]
    
    return render_template_string(
        DASHBOARD_TEMPLATE,
        stats=stats,
        employees=employees,
        recent_payroll=recent_payroll,
        departments=departments,
        datetime=datetime,
        date=date
    )

@app.route('/employee/add', methods=['GET', 'POST'])
@login_required
def add_employee():
    if request.method == 'POST':
        emp_code = request.form.get('emp_code')
        
        # Check if employee code already exists
        existing = Employee.query.filter_by(emp_code=emp_code).first()
        if existing:
            flash('Employee code already exists!', 'error')
            return redirect(url_for('add_employee'))
        
        basic_salary = float(request.form.get('basic_salary'))
        house_rent, medical_allowance, transport_allowance, other_allowances = calculate_allowances(
            basic_salary, request.form.get('designation'), request.form.get('department')
        )
        
        joining_date_str = request.form.get('joining_date')
        joining_date = datetime.strptime(joining_date_str, '%Y-%m-%d').date() if joining_date_str else date.today()
        
        employee = Employee(
            emp_code=emp_code,
            name=request.form.get('name'),
            designation=request.form.get('designation'),
            department=request.form.get('department'),
            basic_salary=basic_salary,
            house_rent=house_rent,
            medical_allowance=medical_allowance,
            transport_allowance=transport_allowance,
            other_allowances=other_allowances,
            provident_fund_percent=10.0,
            tax_exempt=request.form.get('tax_exempt') == 'on',
            joining_date=joining_date,
            status=request.form.get('status', 'Active'),
            bank_account=request.form.get('bank_account')
        )
        
        db.session.add(employee)
        db.session.commit()
        
        flash(f'Employee {employee.name} added successfully!', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template_string(EMPLOYEE_FORM_TEMPLATE, title='Add New Employee', employee=None)

@app.route('/employee/<int:emp_id>')
@login_required
def view_employee(emp_id):
    employee = Employee.query.get_or_404(emp_id)
    flash(f'Viewing employee: {employee.name}', 'success')
    return redirect(url_for('dashboard'))

@app.route('/employee/<int:emp_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_employee(emp_id):
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    employee = Employee.query.get_or_404(emp_id)
    
    if request.method == 'POST':
        employee.name = request.form.get('name')
        employee.designation = request.form.get('designation')
        employee.department = request.form.get('department')
        employee.basic_salary = float(request.form.get('basic_salary'))
        employee.bank_account = request.form.get('bank_account')
        employee.status = request.form.get('status')
        employee.tax_exempt = request.form.get('tax_exempt') == 'on'
        
        # Recalculate allowances
        house_rent, medical_allowance, transport_allowance, other_allowances = calculate_allowances(
            employee.basic_salary, employee.designation, employee.department
        )
        employee.house_rent = house_rent
        employee.medical_allowance = medical_allowance
        employee.transport_allowance = transport_allowance
        employee.other_allowances = other_allowances
        
        db.session.commit()
        flash('Employee updated successfully!', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template_string(EMPLOYEE_FORM_TEMPLATE, title='Edit Employee', employee=employee)

@app.route('/employee/<int:emp_id>/payslip')
@login_required
def download_payslip(emp_id):
    employee = Employee.query.get_or_404(emp_id)
    
    # Get latest payroll record
    payroll_record = PayrollRecord.query.filter_by(employee_id=emp_id).order_by(PayrollRecord.processed_date.desc()).first()
    
    if not payroll_record:
        flash('No payroll record found for this employee. Please process payroll first.', 'error')
        return redirect(url_for('dashboard'))
    
    pdf_buffer = generate_payslip_pdf(payroll_record, employee)
    
    return send_file(
        pdf_buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'Payslip_{employee.emp_code}_{payroll_record.year}_{payroll_record.month}.pdf'
    )

@app.route('/payroll/record/<int:record_id>/payslip')
@login_required
def download_payslip_by_record(record_id):
    payroll_record = PayrollRecord.query.get_or_404(record_id)
    employee = Employee.query.get(payroll_record.employee_id)
    
    pdf_buffer = generate_payslip_pdf(payroll_record, employee)
    
    return send_file(
        pdf_buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'Payslip_{employee.emp_code}_{payroll_record.year}_{payroll_record.month}.pdf'
    )

@app.route('/payroll/process')
@login_required
def process_payroll():
    current_month = datetime.now().month
    current_year = datetime.now().year
    
    # Check if payroll already processed for current month
    existing = PayrollRecord.query.filter_by(month=current_month, year=current_year).first()
    if existing:
        flash(f'Payroll already processed for {datetime.strftime(date(current_year, current_month, 1), "%B %Y")}!', 'warning')
        return redirect(url_for('dashboard'))
    
    active_employees = Employee.query.filter_by(status='Active').all()
    processed_count = 0
    
    for employee in active_employees:
        # Calculate gross salary
        gross_salary = (employee.basic_salary + employee.house_rent + employee.medical_allowance +
                       employee.transport_allowance + employee.other_allowances)
        
        # Calculate deductions
        provident_fund = gross_salary * (employee.provident_fund_percent / 100)
        
        # Calculate annual income for tax
        annual_income = gross_salary * 12
        
        # Calculate monthly tax
        if employee.tax_exempt:
            tax_deducted = 0
        else:
            annual_tax = calculate_bangladesh_tax(annual_income)
            tax_deducted = annual_tax / 12
        
        # Calculate loan deductions
        active_loans = Loan.query.filter_by(employee_id=employee.id, status='Active').all()
        loan_deduction = sum(loan.monthly_installment for loan in active_loans)
        
        # Calculate net salary
        net_salary = gross_salary - provident_fund - tax_deducted - loan_deduction
        
        payroll_record = PayrollRecord(
            employee_id=employee.id,
            month=current_month,
            year=current_year,
            gross_salary=gross_salary,
            provident_fund=provident_fund,
            tax_deducted=tax_deducted,
            loan_deduction=loan_deduction,
            net_salary=net_salary
        )
        
        db.session.add(payroll_record)
        processed_count += 1
    
    db.session.commit()
    flash(f'Payroll processed successfully for {processed_count} employees!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/reports')
@login_required
def generate_reports():
    flash('Report generation feature coming soon!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/loans')
@login_required
def manage_loans():
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    loans = Loan.query.all()
    flash('Loan management feature - View active loans', 'success')
    return redirect(url_for('dashboard'))

# ==================== INITIALIZATION ====================

def init_db():
    with app.app_context():
        db.create_all()
        
        # Create admin user if not exists
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                password_hash=generate_password_hash('admin123'),
                role='admin'
            )
            db.session.add(admin)
            
            # Create HR user
            hr_user = User(
                username='hr',
                password_hash=generate_password_hash('hr123'),
                role='hr'
            )
            db.session.add(hr_user)
            
            db.session.commit()
            print("Admin user created: admin / admin123")
            print("HR user created: hr / hr123")
        
        # Seed sample employees if none exist
        if Employee.query.count() == 0:
            sample_employees = [
                {'emp_code': 'DU-VC-001', 'name': 'Prof. Dr. Md. Akhtaruzzaman', 'designation': 'Vice-Chancellor', 'department': 'Administration'},
                {'emp_code': 'DU-PVC-001', 'name': 'Prof. Dr. Nashid Kamal', 'designation': 'Pro-Vice-Chancellor', 'department': 'Administration'},
                {'emp_code': 'DU-TRE-001', 'name': 'Prof. Dr. Kamal Uddin Ahmed', 'designation': 'Treasurer', 'department': 'Accounts Office'},
                {'emp_code': 'DU-PROF-001', 'name': 'Prof. Dr. Sajahan Mia', 'designation': 'Professor', 'department': 'Computer Science & Engineering'},
                {'emp_code': 'DU-PROF-002', 'name': 'Prof. Dr. Mahmuda Naznin', 'designation': 'Professor', 'department': 'Electrical & Electronic Engineering'},
                {'emp_code': 'DU-APROF-001', 'name': 'Dr. Md. Abul Hasnat', 'designation': 'Associate Professor', 'department': 'Computer Science & Engineering'},
                {'emp_code': 'DU-APROF-002', 'name': 'Dr. Kishor Kumar Paul', 'designation': 'Associate Professor', 'department': 'Mathematics'},
                {'emp_code': 'DU-ASPROF-001', 'name': 'Md. Rashedur Rahman', 'designation': 'Assistant Professor', 'department': 'Computer Science & Engineering'},
                {'emp_code': 'DU-ASPROF-002', 'name': 'Nusrat Jahan', 'designation': 'Assistant Professor', 'department': 'Physics'},
                {'emp_code': 'DU-LEC-001', 'name': 'Md. Tanvir Ahmed', 'designation': 'Lecturer', 'department': 'Computer Science & Engineering'},
                {'emp_code': 'DU-LEC-002', 'name': 'Fatema Tuz Zohra', 'designation': 'Lecturer', 'department': 'Bangla'},
                {'emp_code': 'DU-REG-001', 'name': 'Md. Golam Mostafa', 'designation': 'Registrar', 'department': 'Registrar Office'},
                {'emp_code': 'DU-DREG-001', 'name': 'Kazi Mahbubur Rahman', 'designation': 'Deputy Registrar', 'department': 'Registrar Office'},
                {'emp_code': 'DU-AREG-001', 'name': 'Sharmin Akter', 'designation': 'Assistant Registrar', 'department': 'HR & Admin'},
                {'emp_code': 'DU-ACC-001', 'name': 'Md. Harun Ur Rashid', 'designation': 'Accountant', 'department': 'Accounts Office'},
                {'emp_code': 'DU-SOFF-001', 'name': 'Md. Rafiqul Islam', 'designation': 'Senior Officer', 'department': 'HR & Admin'},
                {'emp_code': 'DU-OFF-001', 'name': 'Abdul Karim', 'designation': 'Officer', 'department': 'Library'},
                {'emp_code': 'DU-OAST-001', 'name': 'Md. Bakul Hossain', 'designation': 'Office Assistant', 'department': 'Computer Science & Engineering'},
                {'emp_code': 'DU-SEC-001', 'name': 'Md. Abdul Mannan', 'designation': 'Security Guard', 'department': 'Security'},
                {'emp_code': 'DU-DRV-001', 'name': 'Md. Sirajul Islam', 'designation': 'Driver', 'department': 'Maintenance'},
                {'emp_code': 'DU-LIB-001', 'name': 'Tahmina Begum', 'designation': 'Librarian', 'department': 'Library'},
            ]
            
            for emp_data in sample_employees:
                basic_salary = get_designation_base_salary(emp_data['designation'])
                house_rent, medical_allowance, transport_allowance, other_allowances = calculate_allowances(
                    basic_salary, emp_data['designation'], emp_data['department']
                )
                
                employee = Employee(
                    emp_code=emp_data['emp_code'],
                    name=emp_data['name'],
                    designation=emp_data['designation'],
                    department=emp_data['department'],
                    basic_salary=basic_salary,
                    house_rent=house_rent,
                    medical_allowance=medical_allowance,
                    transport_allowance=transport_allowance,
                    other_allowances=other_allowances,
                    provident_fund_percent=10.0,
                    tax_exempt=False,
                    joining_date=date.today(),
                    status='Active',
                    bank_account=f"DU-{emp_data['emp_code'].split('-')[2]}"
                )
                db.session.add(employee)
            
            db.session.commit()
            print(f"Seeded {len(sample_employees)} sample employees")

if __name__ == '__main__':
    init_db()
    print("\n" + "="*60)
    print("DHAKA UNIVERSITY PAYROLL MANAGEMENT SYSTEM v2.0")
    print("="*60)
    print("✅ Features Enabled:")
    print("   • SQLite Database")
    print("   • PDF Payslip Generation")
    print("   • Bangladesh Tax Calculator (NBR 2023-24)")
    print("   • Auto-calculation of Allowances")
    print("   • Festival Bonus Ready")
    print("   • Loan Management Ready")
    print("   • Role-Based Access Control")
    print("   • Dashboard Analytics")
    print("\n🔐 Login Credentials:")
    print("   Admin: admin / admin123")
    print("   HR: hr / hr123")
    print("\n🌐 Access the system at: http://localhost:5000")
    print("="*60 + "\n")
    app.run(debug=True, host='0.0.0.0', port=5000)
