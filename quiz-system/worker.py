import pika
import json
import time
import re
from app import app, db
from models import QuizSubmission

# Kunci jawaban yang sudah ditetapkan
MATH_ANSWER_KEYS = {
    "soal_1": "4",
    "soal_2": "7",
    "soal_3": "3",
    "soal_4": "5",
    "soal_5": "2"
}

def clean_answer(answer_str):
    # Membersihkan spasi untuk mentolerir salah ketik (contoh " 4 " menjadi "4")
    return re.sub(r'\s+', '', str(answer_str)).lower()

def callback(ch, method, properties, body):
    message = json.loads(body)
    submission_id = message['submission_id']
    student_answers = message['answers']
    
    print(f"\n[*] Memproses jawaban untuk ID: {submission_id}")
    time.sleep(1) # Beri nafas sedikit agar API selesai menulis ke database
    
    correct_count = 0
    details = {} # Menyimpan riwayat benar/salah
    
    for key, correct_val in MATH_ANSWER_KEYS.items():
        student_val = student_answers.get(key, "") 
        cleaned_student = clean_answer(student_val)
        cleaned_key = clean_answer(correct_val)
        
        if cleaned_student == cleaned_key:
            correct_count += 1
            details[key] = True  # Tandai soal ini BENAR
            print(f"    -> [BENAR] {key}")
        else:
            details[key] = False # Tandai soal ini SALAH
            print(f"    -> [SALAH] {key}: Dijawab '{cleaned_student}', Seharusnya '{cleaned_key}'")
            
    score = correct_count * 20 
    print(f"[*] Kalkulasi Selesai! Skor: {score}. Menyimpan ke database...")
    
    # Proteksi Database (Mencegah Silent Crash)
    try:
        with app.app_context():
            submission = db.session.get(QuizSubmission, submission_id)
            if submission:
                submission.score = score
                submission.status = 'graded'
                submission.details = json.dumps(details) # Simpan riwayat ke DB
                db.session.commit()
                print(f"[v] SUKSES! Data ID: {submission_id} tersimpan.\n")
    except Exception as e:
        print(f"[X] GAGAL menyimpan ke DB: {e}\n")

# --- PERBAIKAN: Logika Kesabaran (Retry Loop) ---
print("Mencoba menghubungi RabbitMQ...")
while True:
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters('rabbitmq'))
        print("Berhasil terhubung ke RabbitMQ!")
        break # Keluar dari loop jika berhasil
    except pika.exceptions.AMQPConnectionError:
        print("RabbitMQ belum siap, mencoba menelepon lagi dalam 5 detik...")
        time.sleep(5) # Jeda 5 detik sebelum mencoba lagi
# ------------------------------------------------

channel = connection.channel()
channel.queue_declare(queue='grading_queue')
channel.basic_consume(queue='grading_queue', on_message_callback=callback, auto_ack=True)

print(' [*] Worker Matematika aktif. Menunggu pesan di antrean...')
channel.start_consuming()