import threading
import requests
import random
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# Target langsung ke pintu gerbang Nginx Load Balancer
URL = "http://localhost:8080/submit"

# Daftar mahasiswa yang sah di sistem RPC worker kita
VALID_STUDENTS = ["MHS-001", "MHS-002", "MHS-003", "MHS-004"]

def send_submission(request_num):
    student_id = random.choice(VALID_STUDENTS)
    
    # Membuat variasi jawaban acak (ada yang benar, ada yang salah)
    payload = {
        "student_id": student_id,
        "answers": {
            "soal_1": str(random.choice([4, 1, 3])),
            "soal_2": str(random.choice([7, 2, 5])),
            "soal_3": str(random.choice([3, 4, 0])),
            "soal_4": str(random.choice([5, 7, 2])),
            "soal_5": str(random.choice([2, 1, 1]))
        }
    }
    
    try:
        t0 = time.time()
        # Menembak Nginx Load Balancer
        response = requests.post(URL, json=payload, timeout=5)
        duration = (time.time() - t0) * 1000  # Hitung latensi dalam mili-detik
        return response.status_code, duration
    except Exception as e:
        return f"ERROR ({type(e).__name__})", 0

def run_stress_test(total_requests=100, concurrency_limit=15):
    print(f"[*] Memulai Stress Test Terdistribusi...")
    print(f"[*] Total Ujian dikirim: {total_requests} submission")
    print(f"[*] Batas Concurrency : {concurrency_limit} thread simultaneous\n")
    
    status_counts = {}
    durations = []
    
    start_time = time.time()
    
    # Membuka ThreadPool untuk menyimulasikan banyak mahasiswa klik tombol bersamaan
    with ThreadPoolExecutor(max_workers=concurrency_limit) as executor:
        futures = [executor.submit(send_submission, i) for i in range(total_requests)]
        
        for future in as_completed(futures):
            status, duration = future.result()
            status_counts[status] = status_counts.get(status, 0) + 1
            if isinstance(status, int):
                durations.append(duration)
                
    end_time = time.time()
    
    # --- CETAK LAPORAN HASIL BEBAN ---
    print("\n" + "="*45)
    print("📊 LAPORAN HASIL STRESS TEST AUTO-GRADER")
    print("="*45)
    print(f"Total Waktu Eksekusi   : {end_time - start_time:.2f} detik")
    print(f"Kecepatan Pemrosesan   : {total_requests / (end_time - start_time):.1f} req/detik")
    print(f"Rekap Hasil HTTP Status:")
    for status, count in status_counts.items():
        status_desc = " (202 Accepted - Lolos Ke RabbitMQ)" if status == 202 else ""
        print(f"  - Status {status}: {count} requests{status_desc}")
        
    if durations:
        avg_latency = sum(durations) / len(durations)
        print(f"Rata-rata Respon REST  : {avg_latency:.2f} ms")
    print("="*45)
    print("[*] Selesai! Silakan intip terminal docker untuk melihat keriuhan para worker.")

if __name__ == "__main__":
    # Menembakkan 1000 request dengan 15 jalur sekaligus
    run_stress_test(total_requests=1000, concurrency_limit=15)