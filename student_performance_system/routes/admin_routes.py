from flask import Blueprint, render_template, request, redirect, url_for, session, flash, send_file
from models.quiz_model import QuizModel
from models.user_model import UserModel

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')
quiz_model = QuizModel()
user_model = UserModel()

@admin_bp.before_request
def require_admin():
    """Require admin role for all admin routes"""
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('auth.login'))

@admin_bp.route('/dashboard')
def dashboard():
    """Admin dashboard"""
    user = user_model.get_user_by_id(session['user_id'])
    
    # Get system statistics
    import sqlite3
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'student'")
    student_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'teacher'")
    teacher_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM quiz_attempts WHERE status = 'completed'")
    total_attempts = cursor.fetchone()[0]
    
    cursor.execute("SELECT AVG(total_score) FROM quiz_attempts WHERE status = 'completed'")
    avg_score = cursor.fetchone()[0] or 0
    
    conn.close()
    
    stats = {
        'students': student_count,
        'teachers': teacher_count,
        'attempts': total_attempts,
        'avg_score': round(avg_score, 2)
    }
    
    return render_template('admin_dashboard.html', user=user, stats=stats)

@admin_bp.route('/manage_users')
def manage_users():
    """Manage students and teachers"""
    students = user_model.get_all_users_by_role('student')
    teachers = user_model.get_all_users_by_role('teacher')
    return render_template('manage_users.html', students=students, teachers=teachers)

@admin_bp.route('/delete_user/<int:user_id>')
def delete_user(user_id):
    """Delete a user"""
    user_model.delete_user(user_id)
    flash('User deleted successfully!', 'success')
    return redirect(url_for('admin.manage_users'))

@admin_bp.route('/analytics')
def analytics():
    """Admin analytics dashboard"""
    data = quiz_model.get_analytics_data(session['user_id'], 'admin')
    return render_template('analytics.html', data=data, role='admin')

@admin_bp.route('/generate_report/<report_type>')
def generate_report(report_type):
    """Generate and download report"""
    if report_type == 'individual':
        # For simplicity, generate report for all students
        output = quiz_model.generate_report('individual')
    elif report_type == 'subject':
        output = quiz_model.generate_report('subject')
    elif report_type == 'class':
        output = quiz_model.generate_report('class')
    else:
        flash('Invalid report type', 'error')
        return redirect(url_for('admin.dashboard'))
    
    return send_file(output, download_name=f'{report_type}_report.xlsx', as_attachment=True)