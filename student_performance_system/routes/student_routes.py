from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from models.quiz_model import QuizModel
from models.user_model import UserModel
from utils.nlp_evaluator import NLPEvaluator
from utils.pdf_parser import PDFParser
from werkzeug.utils import secure_filename
import os
import sqlite3

student_bp = Blueprint('student', __name__, url_prefix='/student')
quiz_model = QuizModel()
user_model = UserModel()
nlp_evaluator = NLPEvaluator()
pdf_parser = PDFParser()

@student_bp.before_request
def require_student():
    """Require student role for all student routes"""
    if 'user_id' not in session or session.get('role') != 'student':
        return redirect(url_for('auth.login'))

@student_bp.route('/dashboard')
def dashboard():
    """Student dashboard"""
    user = user_model.get_user_by_id(session['user_id'])
    subjects = quiz_model.get_student_subjects(session['user_id'])
    results = quiz_model.get_student_results(session['user_id'])
    return render_template('student_dashboard.html', user=user, subjects=subjects, results=results)

@student_bp.route('/select_subjects', methods=['GET', 'POST'])
def select_subjects():
    """Select subject preferences"""
    if request.method == 'POST':
        subject_ids = request.form.getlist('subjects')
        quiz_model.set_student_subjects(session['user_id'], subject_ids)
        flash('Subjects updated successfully!', 'success')
        return redirect(url_for('student.dashboard'))
    
    all_subjects = quiz_model.get_subjects()
    selected_subjects = quiz_model.get_student_subjects(session['user_id'])
    selected_ids = [s['id'] for s in selected_subjects]
    return render_template('select_subjects.html', subjects=all_subjects, selected_ids=selected_ids)

@student_bp.route('/quiz/<int:subject_id>', methods=['GET', 'POST'])
def quiz(subject_id):
    """Take MCQ quiz"""
    if request.method == 'POST':
        attempt_id = request.form.get('attempt_id')
        if not attempt_id:
            attempt_id = quiz_model.start_quiz_attempt(session['user_id'], subject_id)
        
        answers = request.form
        
        mcq_questions = quiz_model.get_mcq_questions(subject_id)
        correct_count = 0
        
        for question in mcq_questions:
            qid = str(question['id'])
            if qid in answers:
                selected = answers[qid]
                # Get correct answer
                conn = sqlite3.connect('database.db')
                cursor = conn.cursor()
                cursor.execute("SELECT correct_answer FROM mcq_questions WHERE id = ?", (question['id'],))
                correct_answer = cursor.fetchone()[0]
                conn.close()
                is_correct = (selected == correct_answer)
                quiz_model.save_mcq_answer(attempt_id, question['id'], selected, is_correct)
                if is_correct:
                    correct_count += 1
        
        # Calculate MCQ score (assuming each question is 1 mark)
        mcq_score = correct_count
        
        # For now, descriptive score is 0, will be updated after PDF evaluation
        quiz_model.update_attempt_scores(attempt_id, mcq_score, 0)
        
        flash('Quiz submitted successfully!', 'success')
        return redirect(url_for('student.quiz_result', attempt_id=attempt_id))
    
    # Create attempt when starting quiz
    attempt_id = quiz_model.start_quiz_attempt(session['user_id'], subject_id)
    mcq_questions = quiz_model.get_mcq_questions(subject_id)
    descriptive_questions = quiz_model.get_descriptive_questions(subject_id)
    return render_template('quiz.html', mcq_questions=mcq_questions, descriptive_questions=descriptive_questions, subject_id=subject_id, attempt_id=attempt_id)

@student_bp.route('/upload_answer/<int:attempt_id>/<int:question_id>', methods=['POST'])
def upload_answer(attempt_id, question_id):
    """Upload PDF answer for descriptive question"""
    if 'pdf_file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['pdf_file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file and file.filename.lower().endswith('.pdf'):
        filename = secure_filename(file.filename)
        filepath = os.path.join('uploads', filename)
        file.save(filepath)
        
        # Extract text from PDF
        extracted_text = pdf_parser.extract_text(filepath)
        
        # Save submission
        quiz_model.save_descriptive_submission(attempt_id, question_id, filepath, extracted_text)
        
        # Evaluate using NLP
        # Get question details
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute("SELECT question, marks, keywords FROM descriptive_questions WHERE id = ?", (question_id,))
        question_data = cursor.fetchone()
        conn.close()
        
        if question_data:
            question_text, marks, keywords = question_data
            score = nlp_evaluator.evaluate_answer(extracted_text, keywords, marks)
            
            # Update score in database
            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()
            cursor.execute("UPDATE descriptive_submissions SET score = ? WHERE attempt_id = ? AND question_id = ?",
                          (score, attempt_id, question_id))
            # Update total score
            cursor.execute("SELECT SUM(score) FROM descriptive_submissions WHERE attempt_id = ?", (attempt_id,))
            desc_score = cursor.fetchone()[0] or 0
            cursor.execute("SELECT mcq_score FROM quiz_attempts WHERE id = ?", (attempt_id,))
            mcq_score = cursor.fetchone()[0] or 0
            total_score = mcq_score + desc_score
            cursor.execute("UPDATE quiz_attempts SET descriptive_score = ?, total_score = ? WHERE id = ?",
                          (desc_score, total_score, attempt_id))
            conn.commit()
            conn.close()
            
            return jsonify({'success': True, 'score': score})
    
    return jsonify({'error': 'Invalid file type'}), 400

@student_bp.route('/result/<int:attempt_id>')
def quiz_result(attempt_id):
    """View quiz result"""
    # Get attempt details
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("""
        SELECT qa.mcq_score, qa.descriptive_score, qa.total_score, s.name
        FROM quiz_attempts qa
        JOIN subjects s ON qa.subject_id = s.id
        WHERE qa.id = ? AND qa.student_id = ?
    """, (attempt_id, session['user_id']))
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return render_template('result.html', 
                             mcq_score=result[0], 
                             descriptive_score=result[1], 
                             total_score=result[2], 
                             subject=result[3])
    return redirect(url_for('student.dashboard'))

@student_bp.route('/analytics')
def analytics():
    """Student analytics dashboard"""
    data = quiz_model.get_analytics_data(session['user_id'], 'student')
    return render_template('analytics.html', data=data, role='student')