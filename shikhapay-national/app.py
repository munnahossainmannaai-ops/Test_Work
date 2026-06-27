from app import create_app

app = create_app()

if __name__ == '__main__':
    print("🚀 Starting ShikkhaPay - Dhaka University Payroll System")
    print("📊 Version: 12.0 (Guardian Edition)")
    print("🌐 Access at: http://127.0.0.1:5000")
    print("👤 Default Admin: admin / admin123")
    print("👤 Default HR: hr / hr123")
    print("="*60)
    app.run(debug=True, host='0.0.0.0', port=5000)
