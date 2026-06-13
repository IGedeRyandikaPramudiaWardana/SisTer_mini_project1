import os, json, time, random
from flask import Flask, request, jsonify
import requests
import pika
from models import db, QuizSubmission

app = Flask(__name__)

# --- PERUBAHAN 1: Gunakan PostgreSQL dari Environment Variable ---
# Jika DATABASE_URL tidak ditemukan, fallback ke string koneksi postgresql
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
    'DATABASE_URL', 
    'postgresql://quiz_user:quiz_password@db:5432/quiz_db'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

WORKER_NODES = ["http://worker-1:9000", "http://worker-2:9000", "http://worker-3:9000"]

def rpc_call(base_url: str, method: str, params: dict, timeout=2.0):
    payload = {"method": method, "params": params}
    r = requests.post(f"{base_url}/rpc", json=payload, timeout=timeout)
    r.raise_for_status()
    return r.json()

@app.route('/submit', methods=['POST'])
def submit_quiz():
    data = request.json
    student_id = data.get('student_id')
    answers = data.get('answers')

    # 1. Panggil RPC ke Worker untuk verifikasi mahasiswa
    try:
        chosen_worker = random.choice(WORKER_NODES)
        rpc_resp = rpc_call(chosen_worker, "verify_student", {"student_id": student_id})
        if not rpc_resp.get("result", False):
            return jsonify({"error": "Akses Ditolak! Mahasiswa tidak terdaftar."}), 403
    except Exception as e:
        return jsonify({"error": f"Gagal RPC ke Worker: {str(e)}"}), 500

    # 2. Simpan status kuis sebagai "pending" ke PostgreSQL
    new_sub = QuizSubmission(student_id=student_id, answers=json.dumps(answers), status='pending')
    db.session.add(new_sub)
    db.session.commit()

    # 3. Lempar tugas koreksi ke keranjang RabbitMQ
    try:
        # --- PERUBAHAN 2: Ambil host RabbitMQ dari environment ---
        rabbitmq_host = os.getenv('RABBITMQ_HOST', 'rabbitmq')
        conn = pika.BlockingConnection(pika.ConnectionParameters(rabbitmq_host))
        ch = conn.channel()
        
        ch.queue_declare(queue='grading_queue', durable=True)
        message = {'submission_id': new_sub.id, 'answers': answers}
        ch.basic_publish(exchange='', routing_key='grading_queue', 
                         body=json.dumps(message),
                         properties=pika.BasicProperties(delivery_mode=2))
        conn.close()
    except Exception as e:
        return jsonify({"error": f"RabbitMQ Error: {str(e)}"}), 500

    return jsonify({"message": "Terkirim", "submission_id": new_sub.id, "status": "pending"}), 202

@app.route('/result/<int:submission_id>', methods=['GET'])
def get_result(submission_id):
    sub = db.session.get(QuizSubmission, submission_id)
    if not sub:
        return jsonify({"error": "Not found"}), 404
    return jsonify({
        "status": sub.status,
        "score": sub.score,
        "details": json.loads(sub.details) if sub.details else None
    })

if __name__ == "__main__":
    with app.app_context():
        # Looping untuk menunggu PostgreSQL benar-benar siap
        retries = 10
        while retries > 0:
            try:
                db.create_all()
                print("✅ [API] Tabel database berhasil disiapkan!")
                break
            except Exception as e:
                error_msg = str(e)
                # Jika tabrakan karena balapan buat tabel, anggap sukses
                if "UniqueViolation" in error_msg or "already exists" in error_msg:
                    print("✅ [API] Tabel sudah dibuat oleh node lain.")
                    break
                
                print(f"⏳ [API] Menunggu Database siap... (Sisa percobaan: {retries})")
                time.sleep(3)
                retries -= 1
                
    app.run(host="0.0.0.0", port=5000, threaded=True)