import requests
import concurrent.futures
import time

url = "http://127.0.0.1:8080/submit" 

def send_quiz(i):
    data = {
        "student_id": "MHS-001",
        "answers": {
            "soal_1": "4", "soal_2": "7", "soal_3": "9", "soal_4": "5", "soal_5": "2" 
        }
    }
    try:
        response = requests.post(url, json=data)
        if response.status_code == 202:
            print(f"[+] Sukses mengirim Ujian Mahasiswa ke-{i}")
        else:
            # TAMPILKAN ERROR ASLINYA JIKA GAGAL
            print(f"[-] Gagal ke-{i} | Status: {response.status_code} | Pesan: {response.text}")
    except Exception as e:
        print(f"[X] Jaringan putus: {e}")

if __name__ == "__main__":
    print("🚀 MEMULAI SERANGAN 1000 REQUEST KE LOAD BALANCER NGINX...")
    start_time = time.time()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        executor.map(send_quiz, range(1, 1001))
            
    end_time = time.time()
    print(f"\n✅ Selesai mengirim 1000 ujian dalam {end_time - start_time:.2f} detik!")