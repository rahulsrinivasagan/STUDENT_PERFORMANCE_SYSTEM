import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

class UserModel:
    def __init__(self, db_path='database.db'):
        self.db_path = db_path
    
    def create_user(self, username, password, role, email=None):
        """Create a new user in the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        hashed_password = generate_password_hash(password)
        try:
            cursor.execute("INSERT INTO users (username, password, role, email) VALUES (?, ?, ?, ?)",
                          (username, hashed_password, role, email))
            conn.commit()
            user_id = cursor.lastrowid
            conn.close()
            return user_id
        except sqlite3.IntegrityError:
            conn.close()
            return None
    
    def authenticate_user(self, username, password):
        """Authenticate user and return user data if valid"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id, password, role FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        conn.close()
        if user and check_password_hash(user[1], password):
            return {'id': user[0], 'role': user[2]}
        return None
    
    def get_user_by_id(self, user_id):
        """Get user details by ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, role, email FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        conn.close()
        if user:
            return {'id': user[0], 'username': user[1], 'role': user[2], 'email': user[3]}
        return None
    
    def get_all_users_by_role(self, role):
        """Get all users by role"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, email FROM users WHERE role = ?", (role,))
        users = cursor.fetchall()
        conn.close()
        return [{'id': u[0], 'username': u[1], 'email': u[2]} for u in users]
    
    def delete_user(self, user_id):
        """Delete a user by ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        conn.close()