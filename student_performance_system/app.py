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
        name TEXT NOT NULL UNIQUE,
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
        FOREIGN KEY (created_by) REFERENCES users(id),
        UNIQUE(subject_id, question)
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
        FOREIGN KEY (created_by) REFERENCES users(id),
        UNIQUE(subject_id, question)
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
    subjects = ['Mathematics', 'Science', 'English', 'History', 'Geography']
    for subject in subjects:
        cursor.execute("INSERT OR IGNORE INTO subjects (name) VALUES (?)", (subject,))
    
    # Add sample teacher and students
    sample_users = [
        ('teacher1', 'teacher123', 'teacher', 'teacher1@example.com'),
        ('student1', 'student123', 'student', 'student1@example.com'),
        ('student2', 'student123', 'student', 'student2@example.com'),
        ('student3', 'student123', 'student', 'student3@example.com')
    ]
    for username, password, role, email in sample_users:
        try:
            cursor.execute("INSERT INTO users (username, password, role, email) VALUES (?, ?, ?, ?)",
                          (username, generate_password_hash(password), role, email))
        except sqlite3.IntegrityError:
            pass

    # Add sample MCQ questions
    sample_mcqs = [
        (1, 'What is 2+2?', '3', '4', '5', '6', 'B', 1),
        (2, 'Which planet is known as the Red Planet?', 'Earth', 'Mars', 'Jupiter', 'Venus', 'B', 1),
        (3, 'Choose the correct synonym of "quick".', 'Slow', 'Fast', 'Bad', 'Ugly', 'B', 1),
        (4, 'Who discovered America?', 'Columbus', 'Newton', 'Edison', 'Galileo', 'A', 1),
        (5, 'What is the capital of France?', 'London', 'Berlin', 'Rome', 'Paris', 'D', 1)
    ]
    for mcq in sample_mcqs:
        cursor.execute("INSERT OR IGNORE INTO mcq_questions (subject_id, question, option_a, option_b, option_c, option_d, correct_answer, created_by) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", mcq)

    # Add sample descriptive questions
    sample_desc = [
        (1, 'Explain Pythagoras theorem', 10, 'right triangle,hypotenuse,squares', 1),
        (2, 'Describe the water cycle', 10, 'evaporation,condensation,precipitation,collection', 1),
        (3, 'What are the main types of sentences in English?', 10, 'declarative,interrogative,imperative,exclamatory', 1),
        (4, 'Why is history important for society?', 10, 'culture,identity,lessons,heritage', 1),
        (5, 'Explain the importance of maps in geography.', 10, 'location,navigation,scale,features', 1)
    ]
    for desc in sample_desc:
        cursor.execute("INSERT OR IGNORE INTO descriptive_questions (subject_id, question, marks, keywords, created_by) VALUES (?, ?, ?, ?, ?)", desc)

    # Link student sample subjects
    cursor.execute("SELECT id FROM users WHERE username = 'student1'")
    student1_id = cursor.fetchone()[0]
    cursor.execute("SELECT id FROM users WHERE username = 'student2'")
    student2_id = cursor.fetchone()[0]
    cursor.execute("SELECT id FROM subjects WHERE name = 'Mathematics'")
    math_id = cursor.fetchone()[0]
    cursor.execute("SELECT id FROM subjects WHERE name = 'Science'")
    science_id = cursor.fetchone()[0]
    cursor.execute("SELECT id FROM subjects WHERE name = 'English'")
    english_id = cursor.fetchone()[0]
    cursor.execute("SELECT id FROM subjects WHERE name = 'History'")
    history_id = cursor.fetchone()[0]
    cursor.execute("SELECT id FROM subjects WHERE name = 'Geography'")
    geography_id = cursor.fetchone()[0]

    for subject_id in [math_id, science_id, english_id]:
        cursor.execute("INSERT OR IGNORE INTO student_subjects (student_id, subject_id) VALUES (?, ?)", (student1_id, subject_id))
    for subject_id in [science_id, english_id, history_id, geography_id]:
        cursor.execute("INSERT OR IGNORE INTO student_subjects (student_id, subject_id) VALUES (?, ?)", (student2_id, subject_id))

    # Add sample completed quiz attempts only when none exist
    cursor.execute("SELECT COUNT(*) FROM quiz_attempts")
    existing_attempts = cursor.fetchone()[0]
    if existing_attempts == 0:
        sample_attempts = [
            (student1_id, math_id, 4, 8, 12, 'completed'),
            (student1_id, science_id, 3, 9, 12, 'completed'),
            (student2_id, english_id, 5, 8, 13, 'completed'),
            (student2_id, history_id, 2, 7, 9, 'completed'),
            (student2_id, geography_id, 4, 9, 13, 'completed')
        ]
        for attempt in sample_attempts:
            cursor.execute("INSERT INTO quiz_attempts (student_id, subject_id, mcq_score, descriptive_score, total_score, status) VALUES (?, ?, ?, ?, ?, ?)", attempt)
            attempt_id = cursor.lastrowid
            # Save one representative MCQ answer row for analytics completeness
            cursor.execute("INSERT INTO mcq_answers (attempt_id, question_id, selected_answer, is_correct) VALUES (?, ?, ?, ?)",
                          (attempt_id, 1, 'B', 1))
            cursor.execute("INSERT INTO descriptive_submissions (attempt_id, question_id, pdf_path, extracted_text, score, feedback, evaluated_at) VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)",
                          (attempt_id, 1, '', 'Sample answer text', attempt[3], 'Auto sample',))

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