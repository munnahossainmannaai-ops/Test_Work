# DU Payroll Management System

A comprehensive Payroll Management System built for the **University of Dhaka**, Bangladesh's oldest and most prestigious university.

## 🏛️ About

This system is designed to manage all payroll-related activities for University of Dhaka employees, including:
- Employee management
- Salary processing
- Leave management
- Loan management
- Reports and analytics

## ✨ Features

### Employee Management
- Add, edit, and delete employee records
- Track employee information (personal, professional, salary)
- Support for different employee types (Permanent, Contractual, Temporary, Visiting)
- Department and designation management

### Payroll Processing
- Monthly salary processing
- Automatic calculation of gross pay, deductions, and net pay
- Support for various allowances (House Rent, Medical, Transport, etc.)
- Tax deduction and provident fund management
- Bonus and overtime payment tracking

### Leave Management
- Multiple leave types (Annual, Sick, Casual, Maternity, Paternity, Study, Unpaid)
- Leave application and approval workflow
- Leave balance tracking

### Loan Management
- Different loan types (House, Car, Personal, Education)
- Loan application and approval process
- Monthly installment tracking
- Loan repayment management

### Reports & Analytics
- Payroll summary reports
- Employee summary by department
- Leave reports with statistics
- Loan reports with outstanding balances

### Security & Access Control
- Role-based access (Admin, HR, Employee)
- Secure authentication
- Audit trail for tracking changes

## 🚀 Getting Started

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Installation

1. **Clone or navigate to the project directory:**
   ```bash
   cd du-payroll-system
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application:**
   ```bash
   python app.py
   ```

5. **Access the application:**
   Open your browser and navigate to `http://localhost:5000`

### Default Login Credentials

```
Username: admin
Password: admin123
```

**⚠️ Important:** Change the default password immediately after first login!

## 📁 Project Structure

```
du-payroll-system/
├── app.py                 # Main application entry point
├── config/                # Configuration files
│   └── __init__.py
├── src/                   # Source code
│   ├── models.py          # Database models
│   ├── forms.py           # WTForms definitions
│   ├── routes.py          # Main routes
│   ├── routes_employees.py
│   ├── routes_payroll.py
│   ├── routes_leaves.py
│   ├── routes_loans.py
│   └── routes_reports.py
├── templates/             # HTML templates
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   ├── dashboard.html
│   ├── employees/
│   ├── payroll/
│   ├── leaves/
│   ├── loans/
│   └── reports/
├── static/                # Static files
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── main.js
├── tests/                 # Test files
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## 💼 User Roles

### Administrator
- Full system access
- User management
- System configuration
- All reports and analytics

### HR Manager
- Employee management
- Payroll processing
- Leave approval
- Loan approval
- Report generation

### Employee
- View personal information
- View payslips
- Apply for leaves
- Apply for loans
- View leave and loan status

## 🎨 Design Features

- **Responsive Design**: Works on desktop, tablet, and mobile devices
- **Bangladesh Theme**: Uses Bangladesh national colors (Green and Red)
- **User-Friendly Interface**: Intuitive navigation and clean layout
- **Real-time Calculations**: Automatic payroll calculations
- **Search & Filter**: Easy data retrieval

## 🔧 Configuration

Edit `config/__init__.py` to customize:
- Database settings
- Session timeout
- Tax rates
- Provident fund rates
- Gratuity rates
- Pagination settings

## 📊 Database

The system uses SQLite by default (for development). For production, configure PostgreSQL or MySQL in the `DATABASE_URL` environment variable.

## 🔐 Security Considerations

- Password hashing using Werkzeug
- CSRF protection via Flask-WTF
- SQL injection prevention via SQLAlchemy ORM
- Role-based access control
- Session management

## 📝 License

This project is developed specifically for the University of Dhaka.

## 👨‍💻 Support

For technical support, please contact the system administrator.

---

**Developed with ❤️ for University of Dhaka**

*Version 1.0 - 2024*
