from flask import Blueprint, render_template, request, redirect, url_for, session, flash, send_file
from models.quiz_model import QuizModel
from models.user_model import UserModel

teacher_bp = Blueprint('teacher', __name__, url_prefix='/teacher')
quiz_model = QuizModel()
user_model = UserModel()

@teacher_bp.before_request
def require_teacher():
    """Require teacher role for all teacher routes"""
    if 'user_id' not in session or session.get('role') != 'teacher':
        return redirect(url_for('auth.login'))

@teacher_bp.route('/dashboard')
def dashboard():
    """Teacher dashboard"""
    user = user_model.get_user_by_id(session['user_id'])
    subjects = quiz_model.get_subjects()  # Teachers can manage all subjects
    return render_template('teacher_dashboard.html', user=user, subjects=subjects)

@teacher_bp.route('/add_mcq/<int:subject_id>', methods=['GET', 'POST'])
def add_mcq(subject_id):
    """Add MCQ question"""
    if request.method == 'POST':
        question = request.form['question']
        options = {
            'A': request.form['option_a'],
            'B': request.form['option_b'],
            'C': request.form['option_c'],
            'D': request.form['option_d']
        }
        correct_answer = request.form['correct_answer']
        
        quiz_model.add_mcq_question(subject_id, question, options, correct_answer, session['user_id'])
        flash('MCQ question added successfully!', 'success')
        return redirect(url_for('teacher.dashboard'))
    
    subject = next((s for s in quiz_model.get_subjects() if s['id'] == subject_id), None)
    return render_template('add_mcq.html', subject=subject)

@teacher_bp.route('/add_descriptive/<int:subject_id>', methods=['GET', 'POST'])
def add_descriptive(subject_id):
    """Add descriptive question"""
    if request.method == 'POST':
        question = request.form['question']
        marks = int(request.form['marks'])
        keywords = request.form['keywords']
        
        quiz_model.add_descriptive_question(subject_id, question, marks, keywords, session['user_id'])
        flash('Descriptive question added successfully!', 'success')
        return redirect(url_for('teacher.dashboard'))
    
    subject = next((s for s in quiz_model.get_subjects() if s['id'] == subject_id), None)
    return render_template('add_descriptive.html', subject=subject)

@teacher_bp.route('/view_submissions/<int:subject_id>')
def view_submissions(subject_id):
    """View student submissions for a subject"""
    # Get all attempts for the subject
    import sqlite3
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("""
        SELECT qa.id, u.username, qa.mcq_score, qa.descriptive_score, qa.total_score, qa.attempted_at
        FROM quiz_attempts qa
        JOIN users u ON qa.student_id = u.id
        WHERE qa.subject_id = ? AND qa.status = 'completed'
        ORDER BY qa.attempted_at DESC
    """, (subject_id,))
    submissions = cursor.fetchall()
    conn.close()
    
    subject = next((s for s in quiz_model.get_subjects() if s['id'] == subject_id), None)
    submissions_data = [{
        'attempt_id': s[0],
        'student': s[1],
        'mcq_score': s[2],
        'descriptive_score': s[3],
        'total_score': s[4],
        'attempted_at': s[5]
    } for s in submissions]
    
    return render_template('view_submissions.html', subject=subject, submissions=submissions_data)

@teacher_bp.route('/analytics')
def analytics():
    """Teacher analytics dashboard"""
    data = quiz_model.get_analytics_data(session['user_id'], 'teacher')
    return render_template('analytics.html', data=data, role='teacher')

@teacher_bp.route('/reports/<report_type>')
def view_reports(report_type):
    """View reports with charts"""
    if report_type == 'subject':
        # Get subject-wise performance data
        data = quiz_model.get_subject_performance_data()
    elif report_type == 'class':
        # Get class performance summary
        data = quiz_model.get_class_performance_data()
    else:
        flash('Invalid report type', 'error')
        return redirect(url_for('teacher.dashboard'))
    
    return render_template('reports.html', data=data, report_type=report_type)