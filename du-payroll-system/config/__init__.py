import os
from datetime import timedelta

class Config:
    """Base configuration class"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'du-payroll-secret-key-2024'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///du_payroll.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)
    
    # University Information
    UNIVERSITY_NAME = "University of Dhaka"
    UNIVERSITY_CODE = "DU"
    
    # Payroll Settings
    TAX_RATE = 0.15  # 15% tax rate
    PROVIDENT_FUND_RATE = 0.10  # 10% provident fund
    GRATUITY_RATE = 0.05  # 5% gratuity
    
    # Pagination
    ITEMS_PER_PAGE = 20

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
