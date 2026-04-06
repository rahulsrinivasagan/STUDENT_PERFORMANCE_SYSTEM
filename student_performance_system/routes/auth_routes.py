from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models.user_model import UserModel

auth_bp = Blueprint('auth', __name__)
user_model = UserModel()

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = user_model.authenticate_user(username, password)
        if user:
            session['user_id'] = user['id']
            session['role'] = user['role']
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid credentials', 'error')
    
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Handle user registration - teachers only"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form.get('role')
        email = request.form.get('email')
        
        # Prevent student self-registration
        if role == 'student':
            flash('Students cannot self-register. Please contact your teacher or administrator.', 'warning')
            return redirect(url_for('auth.register'))
        
        user_id = user_model.create_user(username, password, role, email)
        if user_id:
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash('Username already exists', 'error')
    
    return render_template('register.html')