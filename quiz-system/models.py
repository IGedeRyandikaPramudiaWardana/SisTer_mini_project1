from flask_sqlalchemy import SQLAlchemy

# Inisialisasi library database
db = SQLAlchemy()

# Mendefinisikan struktur tabel
class QuizSubmission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(50), nullable=False)
    answers = db.Column(db.Text, nullable=False)          # Menyimpan jawaban kuis
    score = db.Column(db.Integer, nullable=True)          # Kosong di awal karena belum dinilai
    status = db.Column(db.String(20), default='pending')  # Status: 'pending' atau 'graded'
    