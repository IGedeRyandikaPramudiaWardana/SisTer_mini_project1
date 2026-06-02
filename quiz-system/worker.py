import pika
import json
import time
from app import app, db
from models import QuizSubmission

def callback(ch, method, properties, body):
    # Mengambil pesan dari RabbitMQ
    message = json.loads(body)
    submission_id = message['submission_id']
    answers = message['answers']
    
    print(f"[*] Memproses jawaban untuk ID: {submission_id}")
    
    # Simulasi proses penilaian yang butuh waktu (misal: mengecek kecurangan/AI)
    time.sleep(3) 
    
    # Logika penilaian pura-pura (menghitung jumlah karakter jawaban * 2)
    score = len(str(answers)) * 2 
    
    # Menyimpan nilai akhir ke database
    with app.app_context():
        submission = db.session.get(QuizSubmission, submission_id)
        if submission:
            submission.score = score
            submission.status = 'graded'
            db.session.commit()
            print(f"[v] Selesai! ID: {submission_id} dapat nilai {score}")

# Terhubung ke RabbitMQ
connection = pika.BlockingConnection(pika.ConnectionParameters('rabbitmq'))
channel = connection.channel()

# Memastikan antrean 'grading_queue' ada
channel.queue_declare(queue='grading_queue')

# Memberitahu RabbitMQ untuk menggunakan fungsi 'callback' saat ada pesan masuk
channel.basic_consume(queue='grading_queue', on_message_callback=callback, auto_ack=True)

print(' [*] Worker aktif. Menunggu pesan di antrean... Tekan CTRL+C untuk keluar')
channel.start_consuming()