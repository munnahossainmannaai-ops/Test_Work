import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Application configuration class"""
    
    # Basic Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-change-in-production'
    
    # Database configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///shikhapay.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Mail configuration
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'False').lower() in ['true', '1', 'yes']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    
    # File upload settings
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # Security settings
    BCRYPT_LOG_ROUNDS = int(os.environ.get('BCRYPT_LOG_ROUNDS') or 12)
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'False').lower() in ['true', '1', 'yes']
    REMEMBER_COOKIE_SECURE = os.environ.get('REMEMBER_COOKIE_SECURE', 'False').lower() in ['true', '1', 'yes']
    
    # Feature flags
    ENABLE_AI_MODULE = os.environ.get('ENABLE_AI_MODULE', 'True').lower() in ['true', '1', 'yes']
    ENABLE_PWA = os.environ.get('ENABLE_PWA', 'True').lower() in ['true', '1', 'yes']
    ENABLE_GUARDIAN_SECURITY = os.environ.get('ENABLE_GUARDIAN_SECURITY', 'True').lower() in ['true', '1', 'yes']
    
    # National Integration API Keys (Production)
    NBR_API_KEY = os.environ.get('NBR_API_KEY')
    SONALI_BANK_API_KEY = os.environ.get('SONALI_BANK_API_KEY')
    UGC_API_ENDPOINT = os.environ.get('UGC_API_ENDPOINT', 'https://api.ugc.gov.bd/sync')
    NID_API_KEY = os.environ.get('NID_API_KEY')
    
    # Institutional settings
    UNIVERSITY_ID = os.environ.get('UNIVERSITY_ID', 'DU001')
    REGIONAL_HUB = os.environ.get('REGIONAL_HUB', 'Dhaka')
    
    # Admin contacts
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'admin@du.ac.bd')
    SUPPORT_EMAIL = os.environ.get('SUPPORT_EMAIL', 'support@shikhapay.edu.bd')
