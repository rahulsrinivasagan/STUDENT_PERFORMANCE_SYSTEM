# Student Performance Analysis System

A comprehensive web application for managing student quizzes, performance tracking, and analytics.

## Features

- **Multi-role Authentication**: Student, Teacher, and Admin roles
- **Quiz System**: MCQ and descriptive questions with PDF upload support
- **NLP Evaluation**: Automated grading of descriptive answers using keyword matching
- **Analytics Dashboard**: Performance charts and reports using Chart.js
- **Report Generation**: Excel/CSV reports for various metrics
- **File Upload**: PDF handling for descriptive answers

## Tech Stack

- **Backend**: Python Flask
- **Database**: SQLite
- **Frontend**: HTML, CSS, JavaScript
- **Charts**: Chart.js
- **NLP**: NLTK
- **PDF Processing**: PyPDF2

## Installation

1. **Clone or download the project**

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**:
   ```bash
   python app.py
   ```

4. **Access the application**:
   Open your browser and go to `http://localhost:5000`

## Default Users

- **Admin**: username: `admin`, password: `admin123`
- **Sample Data**: The application includes sample subjects and questions

## Project Structure

```
student_performance_system/
│
├── app.py                          # Main Flask application
├── database.db                     # SQLite database
├── requirements.txt                # Python dependencies
│
├── templates/                      # HTML templates
│   ├── base.html
│   ├── login.html
│   ├── register.html
│   ├── student_dashboard.html
│   ├── teacher_dashboard.html
│   ├── admin_dashboard.html
│   ├── quiz.html
│   ├── result.html
│   ├── analytics.html
│   └── ...
│
├── static/                         # Static files
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── script.js
│
├── models/                         # Database models
│   ├── user_model.py
│   └── quiz_model.py
│
├── routes/                         # Route handlers
│   ├── auth_routes.py
│   ├── student_routes.py
│   ├── teacher_routes.py
│   └── admin_routes.py
│
└── utils/                          # Utility functions
    ├── nlp_evaluator.py
    └── pdf_parser.py
```

## Usage

### For Students:
1. Register/Login as a student
2. Select preferred subjects
3. Take quizzes (MCQ + descriptive)
4. Upload PDF answers for descriptive questions
5. View results and analytics

### For Teachers:
1. Register/Login as a teacher
2. Add MCQ and descriptive questions
3. View student submissions
4. Generate performance reports

### For Admins:
1. Login with admin credentials
2. Manage users (students and teachers)
3. View system-wide analytics
4. Generate comprehensive reports

## Key Features Explained

### NLP-Based Evaluation
- Extracts text from uploaded PDF files
- Matches keywords from predefined answer keys
- Assigns scores based on keyword coverage
- Identifies weak areas in student answers

### Analytics Dashboard
- Subject-wise performance charts
- Student progress tracking
- Class performance statistics
- Interactive charts using Chart.js

### Report Generation
- Individual student reports
- Subject-wise performance reports
- Class-wide statistics
- Exportable Excel files

## Security Notes

- Change the default admin password in production
- Use environment variables for sensitive data
- Implement HTTPS in production
- Add input validation and sanitization

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is for educational purposes. Feel free to modify and use as needed.