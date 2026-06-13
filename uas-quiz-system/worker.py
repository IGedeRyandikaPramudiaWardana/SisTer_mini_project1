import os, time, threading, logging, json, re, random
from typing import Dict, Optional
import requests
import pika
from flask import Flask, request, jsonify
from models import db, QuizSubmission
from sqlalchemy.sql import func


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
    'DATABASE_URL', 
    'postgresql://quiz_user:quiz_password@db:5432/quiz_db'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

log_werkzeug = logging.getLogger('werkzeug')
log_werkzeug.setLevel(logging.ERROR)


NODE_NAME = os.getenv("NODE_NAME", "worker-1")
NODE_ID = int(os.getenv("NODE_ID", "1"))
ALL_NODES_RAW = os.getenv("ALL_NODES", "worker-1:1,worker-2:2,worker-3:3")

NODES: Dict[int, str] = {}
for item in [x.strip() for x in ALL_NODES_RAW.split(",") if x.strip()]:
    host, sid = item.split(":")
    NODES[int(sid)] = host

sorted_ids = sorted(list(NODES.keys()))
my_index = sorted_ids.index(NODE_ID)
next_node_id = sorted_ids[(my_index + 1) % len(sorted_ids)]
NEXT_HOST = NODES[next_node_id]

state_lock = threading.Lock()
leader_id: Optional[int] = None
is_leader = False
participant = False

def log(msg: str):
    print(f"[{NODE_NAME} (ID:{NODE_ID})] {msg}", flush=True)

def rpc_call(url: str, method: str, params: dict, timeout=1.5):
    try:
        r = requests.post(f"{url}/rpc", json={"method": method, "params": params}, timeout=timeout)
        r.raise_for_status()
        return r.json()
    except Exception:
        return {}

def become_leader():
    global leader_id, is_leader, participant
    with state_lock:
        leader_id = NODE_ID
        is_leader = True
        participant = False
    log("🌟 SAYA TERPILIH MENJADI LEADER (RING ELECTION) 🌟")
    rpc_call(f"http://{NEXT_HOST}:9000", "coordinator", {"leader_id": leader_id})

def start_election():
    global participant
    with state_lock:
        if participant or leader_id is not None:
            return
        participant = True
    log(f"Mulai RING ELECTION, mengirim ID {NODE_ID} ke {NEXT_HOST}...")
    rpc_call(f"http://{NEXT_HOST}:9000", "election", {"cand_id": NODE_ID})

@app.post("/rpc")
def rpc():
    global leader_id, is_leader, participant
    body = request.get_json(force=True, silent=True) or {}
    method = body.get("method")
    params = body.get("params") or {}

    if method == "verify_student":
        student_id = params.get("student_id", "")
        is_valid = student_id in ["MHS-001", "MHS-002", "MHS-003", "MHS-004"]
        return jsonify({"result": is_valid})

    if method == "election":
        cand_id = int(params.get("cand_id"))
        
        if leader_id is not None:
            return jsonify({"result": "IGNORED", "reason": "Leader sudah ada"})

        log(f"Menerima operan pemilu ID: {cand_id}")
        
        with state_lock:
            if cand_id > NODE_ID:
                participant = True
                threading.Thread(target=rpc_call, args=(f"http://{NEXT_HOST}:9000", "election", {"cand_id": cand_id})).start()
            elif cand_id < NODE_ID and not participant:
                participant = True
                threading.Thread(target=rpc_call, args=(f"http://{NEXT_HOST}:9000", "election", {"cand_id": NODE_ID})).start()
            elif cand_id == NODE_ID:
                become_leader()
        return jsonify({"result": "OK"})

    if method == "coordinator":
        new_leader_id = int(params.get("leader_id"))
        with state_lock:
            participant = False
            if leader_id != new_leader_id:
                leader_id = new_leader_id
                is_leader = (leader_id == NODE_ID)
                log(f"✅ Mengakui Worker {leader_id} sebagai Leader.")
                threading.Thread(target=rpc_call, args=(f"http://{NEXT_HOST}:9000", "coordinator", {"leader_id": leader_id})).start()
        return jsonify({"result": "OK"})

    return jsonify({"error": "Method not found"}), 400

def start_rabbitmq_consumer():
    # 1. Definisikan Kunci Jawaban Matematika yang Valid
    MATH_ANSWER_KEYS = {
        "soal_1": "4",  # 1 + 3
        "soal_2": "7",  # 2 + 5
        "soal_3": "3",  # 4 - 1
        "soal_4": "5",  # 7 - 2
        "soal_5": "2"   # 1 + 1
    }

    while True:
        try:
            rabbitmq_host = os.getenv('RABBITMQ_HOST', 'rabbitmq')
            conn = pika.BlockingConnection(pika.ConnectionParameters(rabbitmq_host))
            ch = conn.channel()
            break
        except Exception:
            time.sleep(3)

    ch.queue_declare(queue='grading_queue', durable=True)
    ch.basic_qos(prefetch_count=1)

    def on_message(ch, method, properties, body):
        msg = json.loads(body.decode("utf-8"))
        sub_id = msg['submission_id']
        ans = msg['answers']
        
        score = 0
        details = {}
        
        # 2. Cocokkan jawaban mahasiswa dengan kunci jawaban asli
        for k, v in MATH_ANSWER_KEYS.items():
            user_answer = str(ans.get(k, "")).strip()
            correct_answer = str(v).strip()
            
            if user_answer == correct_answer:
                score += 20
                details[k] = True   # Kotak akan berwarna HIJAU di frontend
            else:
                details[k] = False  # Kotak akan berwarna MERAH di frontend
                
        time.sleep(0.5) # Simulasi pemrosesan
        
        with app.app_context():
            sub = db.session.get(QuizSubmission, sub_id)
            if sub:
                sub.score = score
                sub.status = 'graded'
                sub.details = json.dumps(details)
                db.session.commit()
                log(f"Berhasil memperbarui DB untuk ID Ujian: {sub_id}")
        
        role = "MANDOR" if is_leader else "KULI"
        log(f"[{role}] Selesai menilai Ujian ID {sub_id} -> Skor Nyata: {score}")
        ch.basic_ack(delivery_tag=method.delivery_tag)

    log("Menunggu ujian dari RabbitMQ...")
    ch.basic_consume(queue='grading_queue', on_message_callback=on_message)
    ch.start_consuming()
def leader_task():
    while True:
        time.sleep(15)
        if is_leader:
            try:
                with app.app_context():
                    avg = db.session.query(func.avg(QuizSubmission.score)).filter(QuizSubmission.status == 'graded').scalar()
                    if avg is not None:
                        log(f"👑 LAPORAN MANDOR: Rata-rata nilai kelas saat ini adalah {avg:.2f}")
            except: pass

def bootstrap():
    time.sleep(6 + (0.5 * NODE_ID)) 
    start_election()

if __name__ == "__main__":
    with app.app_context():
        # Looping untuk menunggu PostgreSQL benar-benar siap
        retries = 10
        while retries > 0:
            try:
                db.create_all()
                print(f"✅ [{NODE_NAME}] Tabel database berhasil disiapkan!")
                break
            except Exception as e:
                error_msg = str(e)
                # Jika tabrakan karena balapan buat tabel, anggap sukses
                if "UniqueViolation" in error_msg or "already exists" in error_msg:
                    print(f"✅ [{NODE_NAME}] Tabel sudah dibuat oleh node lain.")
                    break
                
                print(f"⏳ [{NODE_NAME}] Menunggu Database siap... (Sisa percobaan: {retries})")
                time.sleep(3)
                retries -= 1
                
    threading.Thread(target=bootstrap, daemon=True).start()
    threading.Thread(target=start_rabbitmq_consumer, daemon=True).start()
    threading.Thread(target=leader_task, daemon=True).start()
    
    log(f"Menjalankan service di port 9000, menunjuk tetangga {NEXT_HOST}")
    app.run(host="0.0.0.0", port=9000, threaded=True)