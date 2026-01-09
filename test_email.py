#!/usr/bin/env python3
"""
Test script to verify email functionality
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables before importing app
from dotenv import load_dotenv
load_dotenv()

from app import create_app
from utils.helpers import send_email

def test_email_functionality():
    """
    Test the email sending functionality
    """
    app = create_app()
    
    with app.app_context():
        # Test email configuration
        mail_server = app.config.get('MAIL_SERVER')
        mail_username = app.config.get('MAIL_USERNAME')
        
        print(f"Mail Server: {mail_server}")
        print(f"Mail Username: {mail_username}")
        
        if not mail_server or not mail_username:
            print("Error: Email configuration not found. Please check your .env file.")
            return False
        
        # Test sending an email
        test_email = input("Enter an email address to send a test OTP to: ").strip()
        if not test_email:
            print("No email address provided.")
            return False
            
        subject = "Test OTP from Social Media App"
        body = "This is a test OTP: 123456\nThis code will expire in 5 minutes."
        
        print(f"Attempting to send email to: {test_email}")
        success, error = send_email(subject, test_email, body)
        
        if success:
            print(f"✅ Email sent successfully to {test_email}")
            return True
        else:
            print(f"❌ Failed to send email: {error}")
            return False

if __name__ == "__main__":
    print("Testing email functionality...")
    test_email_functionality()