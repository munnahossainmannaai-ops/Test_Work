#!/usr/bin/env python3
"""
Dhaka University Payroll Management System
A comprehensive system for managing payroll of university employees.
"""

import csv
import os
from datetime import datetime
from typing import Dict, List, Optional

# Data storage files
EMPLOYEES_FILE = "employees.csv"
PAYROLL_FILE = "payroll_records.csv"

# Salary structures based on designation (Base Salary in BDT)
SALARY_STRUCTURE = {
    "Vice-Chancellor": {"base": 500000, "allowance_pct": 0.25},
    "Pro-Vice-Chancellor": {"base": 450000, "allowance_pct": 0.22},
    "Treasurer": {"base": 400000, "allowance_pct": 0.20},
    "Professor": {"base": 180000, "allowance_pct": 0.15},
    "Associate Professor": {"base": 140000, "allowance_pct": 0.12},
    "Assistant Professor": {"base": 100000, "allowance_pct": 0.10},
    "Lecturer": {"base": 70000, "allowance_pct": 0.08},
    "Registrar": {"base": 250000, "allowance_pct": 0.18},
    "Administrator": {"base": 120000, "allowance_pct": 0.10},
    "Accountant": {"base": 80000, "allowance_pct": 0.08},
    "Librarian": {"base": 90000, "allowance_pct": 0.09},
    "Lab Assistant": {"base": 45000, "allowance_pct": 0.05},
    "Office Staff": {"base": 35000, "allowance_pct": 0.05},
    "Security Guard": {"base": 25000, "allowance_pct": 0.03},
    "Driver": {"base": 30000, "allowance_pct": 0.04},
    "Cleaner": {"base": 20000, "allowance_pct": 0.03},
}

# Tax brackets (monthly income in BDT)
TAX_BRACKETS = [
    (300000, 0.0),  # Up to 300,000 yearly (25,000 monthly) - 0%
    (400000, 0.05),  # Next 100,000 - 5%
    (700000, 0.10),  # Next 300,000 - 10%
    (1100000, 0.15),  # Next 400,000 - 15%
    (1600000, 0.20),  # Next 500,000 - 20%
    (float('inf'), 0.25),  # Above 1,600,000 - 25%
]

class Employee:
    def __init__(self, emp_id: str, name: str, designation: str, 
                 department: str, join_date: str, basic_salary: Optional[float] = None):
        self.emp_id = emp_id
        self.name = name
        self.designation = designation
        self.department = department
        self.join_date = join_date
        
        # Use predefined salary structure or custom basic salary
        if designation in SALARY_STRUCTURE:
            self.basic_salary = basic_salary if basic_salary else SALARY_STRUCTURE[designation]["base"]
            self.allowance_pct = SALARY_STRUCTURE[designation]["allowance_pct"]
        else:
            self.basic_salary = basic_salary if basic_salary else 30000
            self.allowance_pct = 0.05
    
    def calculate_allowances(self) -> float:
        """Calculate total allowances based on percentage"""
        return self.basic_salary * self.allowance_pct
    
    def calculate_gross_salary(self) -> float:
        """Calculate gross salary (Basic + Allowances)"""
        return self.basic_salary + self.calculate_allowances()
    
    def calculate_tax(self, gross_salary: float) -> float:
        """Calculate monthly tax based on yearly income brackets"""
        yearly_income = gross_salary * 12
        monthly_tax = 0
        
        remaining = yearly_income
        prev_bracket = 0
        
        for bracket_limit, rate in TAX_BRACKETS:
            if remaining <= 0:
                break
            
            taxable_in_bracket = min(remaining, bracket_limit - prev_bracket)
            if taxable_in_bracket > 0:
                monthly_tax += (taxable_in_bracket * rate) / 12
            
            remaining -= taxable_in_bracket
            prev_bracket = bracket_limit
        
        return monthly_tax
    
    def calculate_provident_fund(self, gross_salary: float) -> float:
        """Calculate provident fund deduction (10% of basic salary)"""
        return self.basic_salary * 0.10
    
    def calculate_net_salary(self) -> float:
        """Calculate net salary after deductions"""
        gross = self.calculate_gross_salary()
        tax = self.calculate_tax(gross)
        pf = self.calculate_provident_fund(gross)
        return gross - tax - pf
    
    def to_dict(self) -> Dict:
        return {
            'emp_id': self.emp_id,
            'name': self.name,
            'designation': self.designation,
            'department': self.department,
            'join_date': self.join_date,
            'basic_salary': self.basic_salary,
            'allowance_pct': self.allowance_pct
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Employee':
        emp = cls(
            emp_id=data['emp_id'],
            name=data['name'],
            designation=data['designation'],
            department=data['department'],
            join_date=data['join_date'],
            basic_salary=float(data['basic_salary'])
        )
        emp.allowance_pct = float(data.get('allowance_pct', 0.05))
        return emp


class PayrollSystem:
    def __init__(self):
        self.employees: Dict[str, Employee] = {}
        self.payroll_records: List[Dict] = []
        self.load_data()
    
    def load_data(self):
        """Load employee and payroll data from CSV files"""
        # Load employees
        if os.path.exists(EMPLOYEES_FILE):
            with open(EMPLOYEES_FILE, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    emp = Employee.from_dict(row)
                    self.employees[emp.emp_id] = emp
        
        # Load payroll records
        if os.path.exists(PAYROLL_FILE):
            with open(PAYROLL_FILE, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                self.payroll_records = list(reader)
    
    def save_employees(self):
        """Save employee data to CSV file"""
        with open(EMPLOYEES_FILE, 'w', newline='', encoding='utf-8') as f:
            if not self.employees:
                return
            
            fieldnames = ['emp_id', 'name', 'designation', 'department', 
                         'join_date', 'basic_salary', 'allowance_pct']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for emp in self.employees.values():
                writer.writerow(emp.to_dict())
    
    def save_payroll(self):
        """Save payroll records to CSV file"""
        with open(PAYROLL_FILE, 'w', newline='', encoding='utf-8') as f:
            if not self.payroll_records:
                return
            
            fieldnames = ['emp_id', 'name', 'month', 'year', 'basic_salary', 
                         'allowances', 'gross_salary', 'tax', 'provident_fund', 
                         'net_salary', 'payment_date']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.payroll_records)
    
    def add_employee(self, emp_id: str, name: str, designation: str, 
                    department: str, join_date: str, basic_salary: Optional[float] = None) -> bool:
        """Add a new employee"""
        if emp_id in self.employees:
            return False
        
        emp = Employee(emp_id, name, designation, department, join_date, basic_salary)
        self.employees[emp_id] = emp
        self.save_employees()
        return True
    
    def remove_employee(self, emp_id: str) -> bool:
        """Remove an employee"""
        if emp_id not in self.employees:
            return False
        
        del self.employees[emp_id]
        self.save_employees()
        return True
    
    def get_employee(self, emp_id: str) -> Optional[Employee]:
        """Get employee by ID"""
        return self.employees.get(emp_id)
    
    def list_employees(self) -> List[Employee]:
        """List all employees"""
        return list(self.employees.values())
    
    def process_payroll(self, emp_id: str, month: int, year: int) -> Optional[Dict]:
        """Process payroll for an employee for a specific month"""
        emp = self.get_employee(emp_id)
        if not emp:
            return None
        
        # Check if already processed
        for record in self.payroll_records:
            if (record['emp_id'] == emp_id and 
                int(record['month']) == month and 
                int(record['year']) == year):
                return None
        
        basic = emp.basic_salary
        allowances = emp.calculate_allowances()
        gross = emp.calculate_gross_salary()
        tax = emp.calculate_tax(gross)
        pf = emp.calculate_provident_fund(gross)
        net = emp.calculate_net_salary()
        
        record = {
            'emp_id': emp_id,
            'name': emp.name,
            'month': month,
            'year': year,
            'basic_salary': round(basic, 2),
            'allowances': round(allowances, 2),
            'gross_salary': round(gross, 2),
            'tax': round(tax, 2),
            'provident_fund': round(pf, 2),
            'net_salary': round(net, 2),
            'payment_date': datetime.now().strftime('%Y-%m-%d')
        }
        
        self.payroll_records.append(record)
        self.save_payroll()
        return record
    
    def generate_payslip(self, emp_id: str, month: int, year: int) -> Optional[str]:
        """Generate a payslip for an employee"""
        record = None
        for r in self.payroll_records:
            if (r['emp_id'] == emp_id and 
                int(r['month']) == month and 
                int(r['year']) == year):
                record = r
                break
        
        if not record:
            return None
        
        emp = self.get_employee(emp_id)
        if not emp:
            return None
        
        month_names = ["January", "February", "March", "April", "May", "June",
                      "July", "August", "September", "October", "November", "December"]
        
        payslip = f"""
{'='*60}
           DHAKA UNIVERSITY - PAYSLIP
{'='*60}
University of Dhaka, Dhaka-1000, Bangladesh
Pay Period: {month_names[month-1]} {year}
Generated On: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
{'-'*60}

EMPLOYEE INFORMATION:
  Employee ID   : {emp.emp_id}
  Name          : {emp.name}
  Designation   : {emp.designation}
  Department    : {emp.department}
  Join Date     : {emp.join_date}

{'-'*60}
EARNINGS:
  Basic Salary           : BDT {record['basic_salary']:>12,.2f}
  Allowances             : BDT {record['allowances']:>12,.2f}
                          ----------------
  GROSS SALARY           : BDT {record['gross_salary']:>12,.2f}
                          ----------------

{'-'*60}
DEDUCTIONS:
  Income Tax             : BDT {record['tax']:>12,.2f}
  Provident Fund (10%)   : BDT {record['provident_fund']:>12,.2f}
                          ----------------
  Total Deductions       : BDT {(record['tax'] + record['provident_fund']):>12,.2f}
                          ----------------

{'='*60}
NET SALARY PAYABLE       : BDT {record['net_salary']:>12,.2f}
{'='*60}

Payment Date: {record['payment_date']}

This is a computer-generated payslip.
For queries, contact: accounts@du.ac.bd
{'='*60}
"""
        return payslip
    
    def get_payroll_summary(self, month: int, year: int) -> Dict:
        """Get payroll summary for a specific month"""
        records = [r for r in self.payroll_records 
                  if int(r['month']) == month and int(r['year']) == year]
        
        if not records:
            return {}
        
        total_basic = sum(float(r['basic_salary']) for r in records)
        total_allowances = sum(float(r['allowances']) for r in records)
        total_gross = sum(float(r['gross_salary']) for r in records)
        total_tax = sum(float(r['tax']) for r in records)
        total_pf = sum(float(r['provident_fund']) for r in records)
        total_net = sum(float(r['net_salary']) for r in records)
        
        return {
            'total_employees': len(records),
            'total_basic': total_basic,
            'total_allowances': total_allowances,
            'total_gross': total_gross,
            'total_tax': total_tax,
            'total_provident_fund': total_pf,
            'total_net': total_net
        }


def display_menu():
    """Display main menu"""
    print("\n" + "="*60)
    print("     DHAKA UNIVERSITY PAYROLL MANAGEMENT SYSTEM")
    print("="*60)
    print("1. Add New Employee")
    print("2. Remove Employee")
    print("3. View Employee Details")
    print("4. List All Employees")
    print("5. Process Monthly Payroll")
    print("6. Generate Payslip")
    print("7. View Payroll Summary")
    print("8. Exit")
    print("="*60)


def main():
    system = PayrollSystem()
    
    # Add some sample employees if none exist
    if not system.employees:
        sample_employees = [
            ("DU001", "Dr. Mohammad Rahman", "Professor", "Computer Science", "2010-01-15"),
            ("DU002", "Dr. Fatema Khatun", "Associate Professor", "Physics", "2012-03-20"),
            ("DU003", "Md. Abdul Karim", "Assistant Professor", "Mathematics", "2015-07-10"),
            ("DU004", "Nasrin Akter", "Lecturer", "English", "2018-01-05"),
            ("DU005", "Md. Rafiqul Islam", "Registrar", "Administration", "2008-06-12"),
            ("DU006", "Salma Begum", "Accountant", "Finance", "2014-09-18"),
            ("DU007", "Abdul Mannan", "Office Staff", "Administration", "2016-02-28"),
            ("DU008", "Karim Uddin", "Security Guard", "Security", "2017-05-15"),
        ]
        
        for emp_data in sample_employees:
            system.add_employee(*emp_data)
        print("Sample employees loaded successfully!")
    
    while True:
        display_menu()
        choice = input("\nEnter your choice (1-8): ").strip()
        
        if choice == '1':
            # Add New Employee
            print("\n--- Add New Employee ---")
            emp_id = input("Employee ID: ").strip()
            if system.get_employee(emp_id):
                print("Error: Employee ID already exists!")
                continue
            
            name = input("Name: ").strip()
            print("\nAvailable Designations:")
            for i, desig in enumerate(SALARY_STRUCTURE.keys(), 1):
                print(f"{i}. {desig}")
            designation = input("Designation: ").strip()
            department = input("Department: ").strip()
            join_date = input("Join Date (YYYY-MM-DD): ").strip()
            
            custom_salary = input("Basic Salary (leave empty for default): ").strip()
            basic_salary = float(custom_salary) if custom_salary else None
            
            if system.add_employee(emp_id, name, designation, department, join_date, basic_salary):
                print("✓ Employee added successfully!")
            else:
                print("✗ Failed to add employee!")
        
        elif choice == '2':
            # Remove Employee
            print("\n--- Remove Employee ---")
            emp_id = input("Enter Employee ID: ").strip()
            if system.remove_employee(emp_id):
                print("✓ Employee removed successfully!")
            else:
                print("✗ Employee not found!")
        
        elif choice == '3':
            # View Employee Details
            print("\n--- Employee Details ---")
            emp_id = input("Enter Employee ID: ").strip()
            emp = system.get_employee(emp_id)
            
            if emp:
                print(f"\nEmployee ID   : {emp.emp_id}")
                print(f"Name          : {emp.name}")
                print(f"Designation   : {emp.designation}")
                print(f"Department    : {emp.department}")
                print(f"Join Date     : {emp.join_date}")
                print(f"Basic Salary  : BDT {emp.basic_salary:,.2f}")
                print(f"Allowances    : BDT {emp.calculate_allowances():,.2f}")
                print(f"Gross Salary  : BDT {emp.calculate_gross_salary():,.2f}")
                print(f"Net Salary    : BDT {emp.calculate_net_salary():,.2f}")
            else:
                print("✗ Employee not found!")
        
        elif choice == '4':
            # List All Employees
            print("\n--- All Employees ---")
            employees = system.list_employees()
            
            if not employees:
                print("No employees found!")
                continue
            
            print(f"\n{'ID':<10} {'Name':<25} {'Designation':<20} {'Department':<15}")
            print("-" * 70)
            for emp in employees:
                print(f"{emp.emp_id:<10} {emp.name:<25} {emp.designation:<20} {emp.department:<15}")
            print(f"\nTotal Employees: {len(employees)}")
        
        elif choice == '5':
            # Process Monthly Payroll
            print("\n--- Process Monthly Payroll ---")
            emp_id = input("Enter Employee ID: ").strip()
            
            try:
                month = int(input("Month (1-12): ").strip())
                year = int(input("Year: ").strip())
            except ValueError:
                print("Invalid month or year!")
                continue
            
            if month < 1 or month > 12:
                print("Invalid month! Must be between 1-12.")
                continue
            
            record = system.process_payroll(emp_id, month, year)
            
            if record:
                print("\n✓ Payroll processed successfully!")
                print(f"Net Salary: BDT {record['net_salary']:,.2f}")
            else:
                print("✗ Failed to process payroll (employee not found or already processed)!")
        
        elif choice == '6':
            # Generate Payslip
            print("\n--- Generate Payslip ---")
            emp_id = input("Enter Employee ID: ").strip()
            
            try:
                month = int(input("Month (1-12): ").strip())
                year = int(input("Year: ").strip())
            except ValueError:
                print("Invalid month or year!")
                continue
            
            payslip = system.generate_payslip(emp_id, month, year)
            
            if payslip:
                print(payslip)
            else:
                print("✗ Payslip not found! Please process payroll first.")
        
        elif choice == '7':
            # View Payroll Summary
            print("\n--- Payroll Summary ---")
            
            try:
                month = int(input("Month (1-12): ").strip())
                year = int(input("Year: ").strip())
            except ValueError:
                print("Invalid month or year!")
                continue
            
            summary = system.get_payroll_summary(month, year)
            
            if summary:
                month_names = ["January", "February", "March", "April", "May", "June",
                              "July", "August", "September", "October", "November", "December"]
                
                print(f"\n{'='*50}")
                print(f"PAYROLL SUMMARY - {month_names[month-1]} {year}")
                print(f"{'='*50}")
                print(f"Total Employees Processed: {summary['total_employees']}")
                print(f"Total Basic Salary       : BDT {summary['total_basic']:,.2f}")
                print(f"Total Allowances         : BDT {summary['total_allowances']:,.2f}")
                print(f"Total Gross Salary       : BDT {summary['total_gross']:,.2f}")
                print(f"Total Tax Deducted       : BDT {summary['total_tax']:,.2f}")
                print(f"Total Provident Fund     : BDT {summary['total_provident_fund']:,.2f}")
                print(f"Total Net Salary Paid    : BDT {summary['total_net']:,.2f}")
                print(f"{'='*50}")
            else:
                print("No payroll records found for the specified period!")
        
        elif choice == '8':
            # Exit
            print("\nThank you for using Dhaka University Payroll Management System!")
            print("Goodbye!\n")
            break
        
        else:
            print("Invalid choice! Please enter a number between 1-8.")


if __name__ == "__main__":
    main()
