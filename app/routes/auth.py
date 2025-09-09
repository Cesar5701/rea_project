import sqlite3
import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required
import passwordmeter

from app.models import User

# The database connection function will be in the main __init__.py, but routes need access to it.
# We will import it from the app package.
from app import get_conn

# Create a Blueprint for authentication routes
auth_bp = Blueprint('auth', __name__, template_folder='../templates')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """
    Route for user registration.
    Handles both displaying the registration form (GET) and processing the registration (POST).
    """
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Validate that the email is from the institutional domain
        if not email.endswith('@alumno.buap.mx'):
            flash('Solo se permiten registros con el correo institucional "@alumno.buap.mx".', 'error')
            return redirect(url_for('auth.register'))
        
        # Check password strength
        strength, _ = passwordmeter.test(password)
        if strength < 0.5:
            flash('La contraseña es muy débil. Por favor, elige una más segura.', 'error')
            return redirect(url_for('auth.register'))
        
        conn = get_conn()
        # Check if the user already exists
        user_exists = conn.execute("SELECT id FROM usuarios WHERE email = ?", (email,)).fetchone()
        if user_exists:
            flash('Ese correo electrónico ya está registrado.', 'error')
            conn.close()
            return redirect(url_for('auth.register'))
        
        # Hash the password and save the new user to the database
        hashed_password = generate_password_hash(password)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO usuarios (email, password_hash) VALUES (?, ?)", (email, hashed_password))
        conn.commit()
        conn.close()
        flash('¡Registro exitoso! Por favor, inicia sesión con tu correo.', 'success')
        return redirect(url_for('auth.login'))
    
    # Display the registration form
    return render_template('register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    Route for user login.
    Handles both displaying the login form (GET) and processing the login (POST).
    """
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        conn = get_conn()
        user_data = conn.execute("SELECT id, email, password_hash, role FROM usuarios WHERE email = ?", (email,)).fetchone()
        conn.close()
        
        # Check if the user exists and the password is correct
        if user_data and check_password_hash(user_data['password_hash'], password):
            user = User(id=user_data['id'], email=user_data['email'], role=user_data['role'])
            login_user(user)
            session.permanent = True
            return redirect(url_for('main.index'))
        else:
            flash('Correo o contraseña incorrectos.', 'error')
            
    # Display the login form
    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """
    Route for user logout.
    Requires the user to be logged in.
    """
    logout_user()
    return redirect(url_for('main.index'))
