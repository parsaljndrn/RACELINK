from flask import Blueprint, render_template, request, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user
from app.models import User, RunnerProfile  
from app import db
from datetime import datetime

auth = Blueprint('auth', __name__)

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        phone = request.form['phone']
        address = request.form['address']
        gender = request.form['gender']
        birthdate = request.form['birthdate']
        emergency_name = request.form['emergency_contact_name']
        emergency_number = request.form['emergency_contact_number']

        # Check if email already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already registered. Please log in.', 'warning')
            return redirect(url_for('auth.register'))

        # Create the user
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(
            name=name,
            email=email,
            password=hashed_password,
            role='runner'  # automatically runner
        )
        db.session.add(new_user)
        db.session.flush()  # flush to get new_user.id before committing

        # Create the runner profile linked to the user
        runner_profile = RunnerProfile(
            user_id=new_user.id,
            address=address,
            phone=phone,
            gender=gender,
            birthdate=datetime.strptime(birthdate, '%Y-%m-%d'),
            emergency_contact_name=emergency_name,
            emergency_contact_number=emergency_number
        )
        db.session.add(runner_profile)
        db.session.commit()

        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/login.html')


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()

        if not user or not check_password_hash(user.password, password):
            flash('Invalid email or password', 'danger')
            return redirect(url_for('auth.login'))

        login_user(user)
        flash(f'Welcome, {user.name}!', 'success')

        # Redirect automatically based on role
        if user.role == 'organizer':
            return redirect(url_for('admin.manage_events'))
        else:
            return redirect(url_for('runner.view_marathons'))

    return render_template('auth/login.html')

@auth.route('/logout')
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.home'))