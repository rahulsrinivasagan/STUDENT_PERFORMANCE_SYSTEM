import sqlite3
import pandas as pd
from io import BytesIO

class QuizModel:
    def __init__(self, db_path='database.db'):
        self.db_path = db_path
    
    def get_subjects(self):
        """Get all subjects"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM subjects")
        subjects = cursor.fetchall()
        conn.close()
        return [{'id': s[0], 'name': s[1]} for s in subjects]
    
    def add_subject(self, name):
        """Add a new subject"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO subjects (name) VALUES (?)", (name,))
        conn.commit()
        subject_id = cursor.lastrowid
        conn.close()
        return subject_id
    
    def get_student_subjects(self, student_id):
        """Get subjects selected by a student"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT s.id, s.name FROM subjects s
            JOIN student_subjects ss ON s.id = ss.subject_id
            WHERE ss.student_id = ?
        """, (student_id,))
        subjects = cursor.fetchall()
        conn.close()
        return [{'id': s[0], 'name': s[1]} for s in subjects]
    
    def set_student_subjects(self, student_id, subject_ids):
        """Set subjects for a student"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM student_subjects WHERE student_id = ?", (student_id,))
        for subject_id in subject_ids:
            cursor.execute("INSERT INTO student_subjects (student_id, subject_id) VALUES (?, ?)",
                          (student_id, subject_id))
        conn.commit()
        conn.close()
    
    def get_mcq_questions(self, subject_id):
        """Get MCQ questions for a subject"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id, question, option_a, option_b, option_c, option_d FROM mcq_questions WHERE subject_id = ?",
                      (subject_id,))
        questions = cursor.fetchall()
        conn.close()
        return [{'id': q[0], 'question': q[1], 'options': {'A': q[2], 'B': q[3], 'C': q[4], 'D': q[5]}} for q in questions]
    
    def add_mcq_question(self, subject_id, question, options, correct_answer, created_by):
        """Add a new MCQ question"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO mcq_questions (subject_id, question, option_a, option_b, option_c, option_d, correct_answer, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (subject_id, question, options['A'], options['B'], options['C'], options['D'], correct_answer, created_by))
        conn.commit()
        question_id = cursor.lastrowid
        conn.close()
        return question_id
    
    def get_descriptive_questions(self, subject_id):
        """Get descriptive questions for a subject"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id, question, marks, keywords FROM descriptive_questions WHERE subject_id = ?",
                      (subject_id,))
        questions = cursor.fetchall()
        conn.close()
        return [{'id': q[0], 'question': q[1], 'marks': q[2], 'keywords': q[3]} for q in questions]
    
    def add_descriptive_question(self, subject_id, question, marks, keywords, created_by):
        """Add a new descriptive question"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO descriptive_questions (subject_id, question, marks, keywords, created_by)
            VALUES (?, ?, ?, ?, ?)
        """, (subject_id, question, marks, keywords, created_by))
        conn.commit()
        question_id = cursor.lastrowid
        conn.close()
        return question_id
    
    def start_quiz_attempt(self, student_id, subject_id):
        """Start a new quiz attempt"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO quiz_attempts (student_id, subject_id) VALUES (?, ?)",
                      (student_id, subject_id))
        attempt_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return attempt_id
    
    def save_mcq_answer(self, attempt_id, question_id, selected_answer, is_correct):
        """Save MCQ answer"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO mcq_answers (attempt_id, question_id, selected_answer, is_correct)
            VALUES (?, ?, ?, ?)
        """, (attempt_id, question_id, selected_answer, is_correct))
        conn.commit()
        conn.close()
    
    def save_descriptive_submission(self, attempt_id, question_id, pdf_path, extracted_text):
        """Save descriptive submission"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO descriptive_submissions (attempt_id, question_id, pdf_path, extracted_text)
            VALUES (?, ?, ?, ?)
        """, (attempt_id, question_id, pdf_path, extracted_text))
        conn.commit()
        conn.close()
    
    def update_attempt_scores(self, attempt_id, mcq_score, descriptive_score):
        """Update quiz attempt scores"""
        total_score = mcq_score + descriptive_score
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE quiz_attempts SET mcq_score = ?, descriptive_score = ?, total_score = ?, status = 'completed'
            WHERE id = ?
        """, (mcq_score, descriptive_score, total_score, attempt_id))
        conn.commit()
        conn.close()
    
    def get_student_results(self, student_id):
        """Get quiz results for a student"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT qa.id, s.name, qa.mcq_score, qa.descriptive_score, qa.total_score, qa.attempted_at
            FROM quiz_attempts qa
            JOIN subjects s ON qa.subject_id = s.id
            WHERE qa.student_id = ? AND qa.status = 'completed'
            ORDER BY qa.attempted_at DESC
        """, (student_id,))
        results = cursor.fetchall()
        conn.close()
        return [{'id': r[0], 'subject': r[1], 'mcq_score': r[2], 'descriptive_score': r[3], 'total_score': r[4], 'attempted_at': r[5]} for r in results]
    
    def get_analytics_data(self, user_id, role):
        """Get analytics data based on role"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if role == 'student':
            # Student analytics
            cursor.execute("""
                SELECT s.name, AVG(qa.total_score) as avg_score, COUNT(qa.id) as attempts
                FROM quiz_attempts qa
                JOIN subjects s ON qa.subject_id = s.id
                WHERE qa.student_id = ? AND qa.status = 'completed'
                GROUP BY qa.subject_id, s.name
            """, (user_id,))
            data = cursor.fetchall()
            return [{'subject': d[0], 'avg_score': d[1], 'attempts': d[2]} for d in data]
        
        elif role == 'teacher':
            # Teacher analytics - students performance in all subjects
            cursor.execute("""
                SELECT s.name, COUNT(DISTINCT qa.student_id) as students, AVG(qa.total_score) as avg_score
                FROM quiz_attempts qa
                JOIN subjects s ON qa.subject_id = s.id
                WHERE qa.status = 'completed'
                GROUP BY s.id, s.name
            """)
            data = cursor.fetchall()
            return [{'subject': d[0], 'students': d[1], 'avg_score': d[2]} for d in data]
        
        elif role == 'admin':
            # Admin analytics - overall system
            cursor.execute("""
                SELECT s.name, COUNT(qa.id) as total_attempts, AVG(qa.total_score) as avg_score
                FROM quiz_attempts qa
                JOIN subjects s ON qa.subject_id = s.id
                WHERE qa.status = 'completed'
                GROUP BY s.id, s.name
            """)
            data = cursor.fetchall()
            return [{'subject': d[0], 'total_attempts': d[1], 'avg_score': d[2]} for d in data]
        
        conn.close()
        return []
    
    def get_subject_performance_data(self):
        """Get data for subject-wise performance charts"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT s.name, COUNT(qa.id) as attempts, AVG(qa.total_score) as avg_score, 
                   MIN(qa.total_score) as min_score, MAX(qa.total_score) as max_score
            FROM quiz_attempts qa
            JOIN subjects s ON qa.subject_id = s.id
            WHERE qa.status = 'completed'
            GROUP BY s.id, s.name
        """)
        data = cursor.fetchall()
        conn.close()
        return [{'subject': d[0], 'attempts': d[1], 'avg_score': d[2], 'min_score': d[3], 'max_score': d[4]} for d in data]
    
    def get_individual_report_preview(self, limit=10):
        """Get preview rows for individual report"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT u.username, s.name, qa.mcq_score, qa.descriptive_score, qa.total_score, qa.attempted_at
            FROM quiz_attempts qa
            JOIN users u ON qa.student_id = u.id
            JOIN subjects s ON qa.subject_id = s.id
            WHERE qa.status = 'completed'
            ORDER BY qa.attempted_at DESC
            LIMIT ?
        """, (limit,))
        data = cursor.fetchall()
        conn.close()
        return [
            {
                'username': d[0],
                'subject': d[1],
                'mcq_score': d[2],
                'descriptive_score': d[3],
                'total_score': d[4],
                'attempted_at': d[5],
            }
            for d in data
        ]
    
    def get_subject_report_preview(self, limit=10):
        """Get preview rows for subject report"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT s.name, u.username, qa.mcq_score, qa.descriptive_score, qa.total_score, qa.attempted_at
            FROM quiz_attempts qa
            JOIN users u ON qa.student_id = u.id
            JOIN subjects s ON qa.subject_id = s.id
            WHERE qa.status = 'completed'
            ORDER BY qa.attempted_at DESC
            LIMIT ?
        """, (limit,))
        data = cursor.fetchall()
        conn.close()
        return [
            {
                'subject': d[0],
                'student': d[1],
                'mcq_score': d[2],
                'descriptive_score': d[3],
                'total_score': d[4],
                'attempted_at': d[5],
            }
            for d in data
        ]
    
    def get_class_report_preview(self):
        """Get preview rows for class report"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT s.name, COUNT(qa.id) as attempts, AVG(qa.total_score) as avg_score, MIN(qa.total_score) as min_score, MAX(qa.total_score) as max_score
            FROM quiz_attempts qa
            JOIN subjects s ON qa.subject_id = s.id
            WHERE qa.status = 'completed'
            GROUP BY s.id, s.name
            ORDER BY s.name ASC
        """)
        data = cursor.fetchall()
        conn.close()
        return [
            {
                'subject': d[0],
                'attempts': d[1],
                'avg_score': d[2],
                'min_score': d[3],
                'max_score': d[4],
            }
            for d in data
        ]
    
    def get_class_performance_data(self):
        """Get data for class performance summary"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT u.username, COUNT(qa.id) as attempts, AVG(qa.total_score) as avg_score,
                   SUM(qa.mcq_score) as total_mcq, SUM(qa.descriptive_score) as total_descriptive
            FROM quiz_attempts qa
            JOIN users u ON qa.student_id = u.id
            WHERE qa.status = 'completed' AND u.role = 'student'
            GROUP BY u.id, u.username
        """)
        data = cursor.fetchall()
        conn.close()
        return [{'student': d[0], 'attempts': d[1], 'avg_score': d[2], 'total_mcq': d[3], 'total_descriptive': d[4]} for d in data]
    
    def generate_report(self, report_type, filters=None):
        """Generate Excel report"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            if report_type == 'individual':
                query = """
                    SELECT u.username, s.name, qa.mcq_score, qa.descriptive_score, qa.total_score, qa.attempted_at
                    FROM quiz_attempts qa
                    JOIN users u ON qa.student_id = u.id
                    JOIN subjects s ON qa.subject_id = s.id
                    WHERE qa.status = 'completed'
                """
                if filters and 'student_id' in filters:
                    query += f" AND qa.student_id = {filters['student_id']}"
            
            elif report_type == 'subject':
                query = """
                    SELECT s.name, u.username, qa.mcq_score, qa.descriptive_score, qa.total_score, qa.attempted_at
                    FROM quiz_attempts qa
                    JOIN users u ON qa.student_id = u.id
                    JOIN subjects s ON qa.subject_id = s.id
                    WHERE qa.status = 'completed'
                """
                if filters and 'subject_id' in filters:
                    query += f" AND qa.subject_id = {filters['subject_id']}"
            
            elif report_type == 'class':
                query = """
                    SELECT s.name, COUNT(qa.id) as attempts, AVG(qa.total_score) as avg_score, MIN(qa.total_score) as min_score, MAX(qa.total_score) as max_score
                    FROM quiz_attempts qa
                    JOIN subjects s ON qa.subject_id = s.id
                    WHERE qa.status = 'completed'
                    GROUP BY s.id, s.name
                """
            
            df = pd.read_sql_query(query, conn)
            conn.close()
            
            if df.empty:
                # Create a dummy dataframe with headers
                if report_type == 'individual':
                    df = pd.DataFrame(columns=['Username', 'Subject', 'MCQ Score', 'Descriptive Score', 'Total Score', 'Attempted At'])
                elif report_type == 'subject':
                    df = pd.DataFrame(columns=['Subject', 'Username', 'MCQ Score', 'Descriptive Score', 'Total Score', 'Attempted At'])
                elif report_type == 'class':
                    df = pd.DataFrame(columns=['Subject', 'Attempts', 'Avg Score', 'Min Score', 'Max Score'])
            
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Report', index=False)
            output.seek(0)
            return output
        except Exception as e:
            raise Exception(f"Error generating report: {str(e)}")