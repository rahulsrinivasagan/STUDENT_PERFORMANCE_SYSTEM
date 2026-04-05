from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
import sqlite3
import os
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename
from models.user_model import UserModel
from models.quiz_model import QuizModel
from routes.auth_routes import auth_bp
from routes.student_routes import student_bp
from routes.teacher_routes import teacher_bp
from routes.admin_routes import admin_bp
from utils.nlp_evaluator import NLPEvaluator
from utils.pdf_parser import PDFParser
import pandas as pd
from io import BytesIO

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Change this in production
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload folder exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(student_bp)
app.register_blueprint(teacher_bp)
app.register_blueprint(admin_bp)

# Initialize database
def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL,
        email TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Subjects table
    cursor.execute('''CREATE TABLE IF NOT EXISTS subjects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Student subjects
    cursor.execute('''CREATE TABLE IF NOT EXISTS student_subjects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER,
        subject_id INTEGER,
        FOREIGN KEY (student_id) REFERENCES users(id),
        FOREIGN KEY (subject_id) REFERENCES subjects(id)
    )''')
    
    # MCQ Questions
    cursor.execute('''CREATE TABLE IF NOT EXISTS mcq_questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subject_id INTEGER,
        question TEXT NOT NULL,
        option_a TEXT NOT NULL,
        option_b TEXT NOT NULL,
        option_c TEXT NOT NULL,
        option_d TEXT NOT NULL,
        correct_answer TEXT NOT NULL,
        created_by INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (subject_id) REFERENCES subjects(id),
        FOREIGN KEY (created_by) REFERENCES users(id)
    )''')
    
    # Descriptive Questions
    cursor.execute('''CREATE TABLE IF NOT EXISTS descriptive_questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subject_id INTEGER,
        question TEXT NOT NULL,
        marks INTEGER NOT NULL,
        keywords TEXT NOT NULL,
        created_by INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (subject_id) REFERENCES subjects(id),
        FOREIGN KEY (created_by) REFERENCES users(id)
    )''')
    
    # Quiz Attempts
    cursor.execute('''CREATE TABLE IF NOT EXISTS quiz_attempts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER,
        subject_id INTEGER,
        mcq_score INTEGER DEFAULT 0,
        descriptive_score INTEGER DEFAULT 0,
        total_score INTEGER DEFAULT 0,
        status TEXT DEFAULT 'in_progress',
        attempted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (student_id) REFERENCES users(id),
        FOREIGN KEY (subject_id) REFERENCES subjects(id)
    )''')
    
    # MCQ Answers
    cursor.execute('''CREATE TABLE IF NOT EXISTS mcq_answers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        attempt_id INTEGER,
        question_id INTEGER,
        selected_answer TEXT,
        is_correct BOOLEAN,
        FOREIGN KEY (attempt_id) REFERENCES quiz_attempts(id),
        FOREIGN KEY (question_id) REFERENCES mcq_questions(id)
    )''')
    
    # Descriptive Submissions
    cursor.execute('''CREATE TABLE IF NOT EXISTS descriptive_submissions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        attempt_id INTEGER,
        question_id INTEGER,
        pdf_path TEXT,
        extracted_text TEXT,
        score INTEGER DEFAULT 0,
        feedback TEXT,
        evaluated_at TIMESTAMP,
        FOREIGN KEY (attempt_id) REFERENCES quiz_attempts(id),
        FOREIGN KEY (question_id) REFERENCES descriptive_questions(id)
    )''')
    
    conn.commit()
    conn.close()

# Initialize sample data
def init_sample_data():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # Add admin user with hashed password
    try:
        hashed_password = generate_password_hash('admin123')
        cursor.execute("INSERT INTO users (username, password, role, email) VALUES (?, ?, ?, ?)",
                      ('admin', hashed_password, 'admin', 'admin@example.com'))
    except sqlite3.IntegrityError:
        # If admin exists, update stored password if it is not hashed
        cursor.execute("SELECT password FROM users WHERE username = 'admin'")
        row = cursor.fetchone()
        if row:
            stored_password = row[0]
            if not stored_password.startswith('pbkdf2:') and not stored_password.startswith('bcrypt:'):
                cursor.execute("UPDATE users SET password = ? WHERE username = ?",
                              (generate_password_hash('admin123'), 'admin'))
    
    # Add sample subjects
    subjects = ['Mathematics', 'Science', 'English', 'History']
    for subject in subjects:
        cursor.execute("INSERT OR IGNORE INTO subjects (name) VALUES (?)", (subject,))
    
    # Add sample MCQ questions
    cursor.execute("INSERT OR IGNORE INTO mcq_questions (subject_id, question, option_a, option_b, option_c, option_d, correct_answer, created_by) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                  (1, 'What is 2+2?', '3', '4', '5', '6', 'B', 1))
    
    # Add sample descriptive question
    cursor.execute("INSERT OR IGNORE INTO descriptive_questions (subject_id, question, marks, keywords, created_by) VALUES (?, ?, ?, ?, ?)",
                  (1, 'Explain Pythagoras theorem', 10, 'right triangle,hypotenuse,squares', 1))
    
    conn.commit()
    conn.close()

@app.route('/')
def index():
    if 'user_id' in session:
        if session['role'] == 'student':
            return redirect(url_for('student.dashboard'))
        elif session['role'] == 'teacher':
            return redirect(url_for('teacher.dashboard'))
        elif session['role'] == 'admin':
            return redirect(url_for('admin.dashboard'))
    return redirect(url_for('auth.login'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))

if __name__ == '__main__':
    init_db()
    init_sample_data()
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)