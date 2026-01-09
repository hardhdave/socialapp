from flask import Blueprint, render_template, request, flash, redirect, url_for, session, current_app
from flask_login import login_user, logout_user, login_required, current_user
from urllib.parse import urlparse as url_parse  # FIXED IMPORT
from werkzeug.security import check_password_hash, generate_password_hash
from models.user import User
from app import db
import secrets
import time
from utils.helpers import send_email

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/test-email', methods=['GET', 'POST'])
@login_required
def test_email():
    if request.method == 'POST':
        to = request.form.get('to') or current_user.email
        success, error = send_email("Sapp test email", to, "This is a test email from Sapp.")
        if success:
            flash(f'Test email sent to {to}.', 'success')
        else:
            flash(f'Failed to send email: {error}', 'error')
        return redirect(url_for('auth.test_email'))
    return render_template('auth/test_email.html')

@auth_bp.route('/forgot', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        user = User.query.filter_by(email=email).first()
        if not user:
            flash('No account found with that email.', 'error')
            return render_template('auth/forgot.html')
        otp_code = f"{secrets.randbelow(1000000):06d}"
        session['reset_user_id'] = user.id
        session['reset_otp'] = otp_code
        session['reset_otp_expiry'] = int(time.time()) + 300
        success, error = send_email("Your Sapp password reset code", user.email, f"Your Sapp password reset code is: {otp_code}\nThis code will expire in 5 minutes.")
        if success:
            flash('We sent a password reset code to your email.', 'info')
        else:
            flash(f'Unable to send email: {error}', 'error')
        return redirect(url_for('auth.reset_verify'))
    return render_template('auth/forgot.html')

@auth_bp.route('/reset-verify', methods=['GET', 'POST'])
def reset_verify():
    user_id = session.get('reset_user_id')
    if not user_id:
        return redirect(url_for('auth.forgot_password'))
    if request.method == 'POST':
        code = request.form.get('code', '').strip()
        stored = session.get('reset_otp')
        expiry = session.get('reset_otp_expiry', 0)
        if not stored or int(time.time()) > int(expiry):
            flash('Code expired. A new code has been sent.', 'error')
            user = User.query.get(user_id)
            if user:
                new_code = f"{secrets.randbelow(1000000):06d}"
                session['reset_otp'] = new_code
                session['reset_otp_expiry'] = int(time.time()) + 300
                send_email("Your Sapp password reset code", user.email, f"Your Sapp password reset code is: {new_code}\nThis code will expire in 5 minutes.")
            return redirect(url_for('auth.reset_verify'))
        if code == stored:
            session['allow_password_reset'] = True
            return redirect(url_for('auth.reset_password'))
        flash('Invalid code. Please try again.', 'error')
    return render_template('auth/verify.html')

@auth_bp.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if not session.get('allow_password_reset') or not session.get('reset_user_id'):
        return redirect(url_for('auth.forgot_password'))
    if request.method == 'POST':
        new_password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        if len(new_password) < 6:
            flash('Password must be at least 6 characters.', 'error')
            return render_template('auth/reset_password.html')
        if new_password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('auth/reset_password.html')
        user = User.query.get(session.get('reset_user_id'))
        if user:
            user.password_hash = generate_password_hash(new_password)
            db.session.commit()
            # Clear reset session
            session.pop('reset_user_id', None)
            session.pop('reset_otp', None)
            session.pop('reset_otp_expiry', None)
            session.pop('allow_password_reset', None)
            flash('Password updated successfully. Please log in.', 'success')
            return redirect(url_for('auth.login'))
        flash('User not found.', 'error')
        return redirect(url_for('auth.forgot_password'))
    return render_template('auth/reset_password.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        username_or_email = request.form.get('username_or_email')
        password = request.form.get('password')
        remember_me = bool(request.form.get('remember_me'))
        
        # Find user by username or email
        user = User.query.filter(
            (User.username == username_or_email) | 
            (User.email == username_or_email)
        ).first()
        
        if user and check_password_hash(user.password_hash, password):
            otp_code = f"{secrets.randbelow(1000000):06d}"
            session['pending_user_id'] = user.id
            session['login_otp'] = otp_code
            session['otp_expiry'] = int(time.time()) + 300  # 5 minutes
            session['remember_me'] = remember_me

            subject = "Your Sapp login code"
            body = f"Your Sapp login code is: {otp_code}\nThis code will expire in 5 minutes.\nIf you did not request this, please ignore."
            success, error = send_email(subject, user.email, body)
            if success:
                flash('We sent a login code to your email. Enter it to continue.', 'info')
            else:
                flash(f'Unable to send email: {error}', 'error')
            return redirect(url_for('auth.verify'))
        else:
            flash('Invalid username/email or password', 'error')
    
    return render_template('auth/login.html')

@auth_bp.route('/verify', methods=['GET', 'POST'])
def verify():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    pending_user_id = session.get('pending_user_id')
    if not pending_user_id:
        return redirect(url_for('auth.login'))
    if request.method == 'POST':
        input_code = request.form.get('code', '').strip()
        stored_code = session.get('login_otp')
        expiry = session.get('otp_expiry', 0)
        if not stored_code or int(time.time()) > int(expiry):
            flash('Code expired. We have sent a new code to your email.', 'error')
            user = User.query.get(pending_user_id)
            if user:
                new_code = f"{secrets.randbelow(1000000):06d}"
                session['login_otp'] = new_code
                session['otp_expiry'] = int(time.time()) + 300
                send_email("Your Sapp login code", user.email, f"Your Sapp login code is: {new_code}\nThis code will expire in 5 minutes.")
            return redirect(url_for('auth.verify'))
        if input_code == stored_code:
            user = User.query.get(pending_user_id)
            if user:
                remember_me = bool(session.get('remember_me'))
                login_user(user, remember=remember_me)
                # Clear session keys
                session.pop('pending_user_id', None)
                session.pop('login_otp', None)
                session.pop('otp_expiry', None)
                session.pop('remember_me', None)
                next_page = request.args.get('next')
                if not next_page or url_parse(next_page).netloc != '':
                    next_page = url_for('main.index')
                flash('Logged in successfully.', 'success')
                return redirect(next_page)
            flash('User not found.', 'error')
            return redirect(url_for('auth.login'))
        else:
            flash('Invalid code. Please try again.', 'error')
    return render_template('auth/verify.html')

@auth_bp.route('/resend-code', methods=['POST'])
def resend_code():
    pending_user_id = session.get('pending_user_id')
    if not pending_user_id:
        return redirect(url_for('auth.login'))
    user = User.query.get(pending_user_id)
    if user:
        new_code = f"{secrets.randbelow(1000000):06d}"
        session['login_otp'] = new_code
        session['otp_expiry'] = int(time.time()) + 300
        success, error = send_email("Your Sapp login code", user.email, f"Your Sapp login code is: {new_code}\nThis code will expire in 5 minutes.")
        if success:
            flash('A new code was sent to your email.', 'info')
        else:
            flash(f'Unable to send email: {error}', 'error')
    return redirect(url_for('auth.verify'))

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        full_name = request.form.get('full_name')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validation
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return render_template('auth/register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return render_template('auth/register.html')
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('auth/register.html')
        
        # Create new user
        user = User(
            username=username,
            email=email,
            full_name=full_name,
            password_hash=generate_password_hash(password)
        )
        
        db.session.add(user)
        db.session.commit()
        
        # Send OTP and redirect to verification
        otp_code = f"{secrets.randbelow(1000000):06d}"
        session['pending_user_id'] = user.id
        session['login_otp'] = otp_code
        session['otp_expiry'] = int(time.time()) + 300
        success, error = send_email("Your Sapp verification code", user.email, f"Your Sapp verification code is: {otp_code}\nThis code will expire in 5 minutes.")
        if not success:
            flash(f'Unable to send email: {error}', 'error')
        flash('We sent a verification code to your email. Enter it to complete sign up.', 'info')
        return redirect(url_for('auth.verify'))
    
    return render_template('auth/register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))
