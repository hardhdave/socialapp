# Email Setup Guide for OTP Functionality

## Overview

This guide explains how to properly configure email settings for OTP (One-Time Password) functionality in the social media app.

## Prerequisites

- A Gmail account (or other SMTP-supported email service)
- Two-factor authentication enabled on your Gmail account
- An App Password generated for the application

## Step-by-Step Setup

### 1. Configure Your Gmail Account

1. Go to your [Google Account settings](https://myaccount.google.com/)
2. Navigate to Security > 2-Step Verification
3. Enable 2-Step Verification if not already enabled
4. Click on "App passwords" under the 2-step verification section
5. Select "Mail" as the app and "Other" as the device (name it "SocialMediaApp")
6. Copy the generated 16-character app password

### 2. Update Environment Variables

Open the `.env` file in the root directory and update these values:

```
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USE_SSL=false
MAIL_USERNAME=your-actual-gmail-address@gmail.com
MAIL_PASSWORD=your-16-character-app-password
```

Replace:

- `your-actual-gmail-address@gmail.com` with your actual Gmail address
- `your-16-character-app-password` with the app password generated in step 1

### 3. Restart the Application

After updating the `.env` file, restart your Flask application for the changes to take effect.

## Troubleshooting

### Common Issues:

1. **Authentication Error**:

   - Ensure you're using an App Password, not your regular Gmail password
   - Verify two-factor authentication is enabled

2. **Connection Timeout**:

   - Check your internet connection
   - Ensure ports 587 or 465 are not blocked by firewall

3. **SSL/TLS Errors**:
   - Make sure `MAIL_USE_TLS=true` and `MAIL_USE_SSL=false` for Gmail
   - For other providers, check their SMTP settings

### Testing Your Configuration:

Run the test script to verify email functionality:

```bash
python test_email.py
```

## Alternative Email Providers

If you're not using Gmail, update the `.env` file with appropriate SMTP settings:

- **Outlook/Hotmail**: `MAIL_SERVER=smtp-mail.outlook.com`, `MAIL_PORT=587`
- **Yahoo**: `MAIL_SERVER=smtp.mail.yahoo.com`, `MAIL_PORT=587`
- **Custom SMTP**: Consult your email provider's SMTP settings

## Security Notes

- Never commit your `.env` file to version control
- Store the `.env` file securely and restrict access
- Regularly rotate your App Password for security

## OTP Functionality

Once properly configured, the app will use this email system for:

- User registration verification
- Login verification codes
- Password reset codes
- Other OTP-based authentication flows
