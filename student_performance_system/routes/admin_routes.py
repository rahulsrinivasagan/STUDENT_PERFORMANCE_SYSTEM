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
    deleted_students = user_model.get_deleted_users_by_role('student')
    deleted_teachers = user_model.get_deleted_users_by_role('teacher')
    return render_template('manage_users.html', students=students, teachers=teachers, deleted_students=deleted_students, deleted_teachers=deleted_teachers)

@admin_bp.route('/add_user', methods=['GET', 'POST'])
def add_user():
    """Add new student or teacher"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        email = request.form.get('email')
        
        user_id = user_model.create_user(username, password, role, email)
        if user_id:
            flash(f'{role.capitalize()} {username} added successfully!', 'success')
        else:
            flash('Username already exists', 'error')
        return redirect(url_for('admin.manage_users'))
    
    return render_template('add_user.html')

@admin_bp.route('/delete_user/<int:user_id>')
def delete_user(user_id):
    """Soft delete a user (mark as deleted)"""
    user_model.soft_delete_user(user_id)
    flash('User deleted successfully!', 'success')
    return redirect(url_for('admin.manage_users'))

@admin_bp.route('/restore_user/<int:user_id>')
def restore_user(user_id):
    """Restore a deleted user"""
    user_model.restore_user(user_id)
    flash('User restored successfully!', 'success')
    return redirect(url_for('admin.manage_users'))

@admin_bp.route('/analytics')
def analytics():
    """Admin analytics dashboard"""
    data = quiz_model.get_analytics_data(session['user_id'], 'admin')
    return render_template('analytics.html', data=data, role='admin')

@admin_bp.route('/view_reports/<report_type>')
def view_reports(report_type):
    """View report preview"""
    valid_types = ['individual', 'subject', 'class']
    if report_type not in valid_types:
        flash('Invalid report type', 'error')
        return redirect(url_for('admin.dashboard'))

    if report_type == 'individual':
        preview_data = quiz_model.get_individual_report_preview()
    elif report_type == 'subject':
        preview_data = quiz_model.get_subject_report_preview()
    else:
        preview_data = quiz_model.get_class_report_preview()

    preview_data = preview_data or []
    return render_template('admin_reports.html', report_type=report_type, preview_data=preview_data)

@admin_bp.route('/download_report/<report_type>')
def download_report(report_type):
    """Generate and download report"""
    if report_type == 'individual':
        output = quiz_model.generate_report('individual')
    elif report_type == 'subject':
        output = quiz_model.generate_report('subject')
    elif report_type == 'class':
        output = quiz_model.generate_report('class')
    else:
        flash('Invalid report type', 'error')
        return redirect(url_for('admin.dashboard'))
    
    return send_file(output, download_name=f'{report_type}_report.xlsx', as_attachment=True)