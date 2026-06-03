from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class QuizSubmission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(50), nullable=False)
    answers = db.Column(db.Text, nullable=False)
    score = db.Column(db.Integer, nullable=True)
    status = db.Column(db.String(20), default='pending')
    details = db.Column(db.Text, nullable=True)