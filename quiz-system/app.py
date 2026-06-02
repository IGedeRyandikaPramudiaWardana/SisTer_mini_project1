from flask import Flask, request, jsonify
from models import db, QuizSubmission
import pika
import json
import xmlrpc.client  # <-- Tambahkan library RPC ini

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quiz.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Menghubungkan ke User Service via RPC di port 8000
rpc_client = xmlrpc.client.ServerProxy("http://rpc_user_service:8000/")

@app.route('/', methods=['GET'])
def home():
    return "Server Kuis Aktif! Gunakan endpoint /submit (POST) untuk mengirim jawaban."

@app.route('/submit', methods=['POST'])
def submit_quiz():
    data = request.json
    student_id = data.get('student_id')
    answers = data.get('answers')

    # --- TAHAP 4: Validasi menggunakan RPC ---
    try:
        # Memanggil fungsi verify_student yang ada di user_service.py
        is_valid = rpc_client.verify_student(student_id)
        if not is_valid:
            return jsonify({"error": "Akses Ditolak! Mahasiswa tidak terdaftar."}), 403
    except Exception as e:
        return jsonify({"error": f"Gagal terhubung ke layanan otentikasi/RPC: {str(e)}"}), 500
    # -----------------------------------------

    # 1. Simpan ke database
    new_submission = QuizSubmission(student_id=student_id, answers=str(answers), status='pending')
    db.session.add(new_submission)
    db.session.commit()

    # 2. Kirim pesan ke RabbitMQ
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters('rabbitmq'))
        channel = connection.channel()
        channel.queue_declare(queue='grading_queue')
        
        message = {'submission_id': new_submission.id, 'answers': answers}
        channel.basic_publish(exchange='', routing_key='grading_queue', body=json.dumps(message))
        connection.close()
    except Exception as e:
        return jsonify({"error": f"Gagal menghubungi RabbitMQ: {str(e)}"}), 500

    # 3. Beri respons sukses
    return jsonify({
        "message": "Jawaban diterima dan divalidasi!",
        "submission_id": new_submission.id,
        "status": "pending"
    }), 202

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', debug=True, port=5000)