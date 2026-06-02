import requests
import concurrent.futures
import time

url = "http://127.0.0.1:5000/submit"

# Fungsi untuk mengirim satu kuis
def send_quiz(i):
    data = {
        "student_id": f"MHS-{i}",
        "answers": f"Ini adalah jawaban dari mahasiswa nomor urut {i}"
    }
    try:
        response = requests.post(url, json=data)
        print(f"Mahasiswa {i} submit: Status {response.status_code}")
    except Exception as e:
        print(f"Mahasiswa {i} gagal: {e}")

# Fungsi utama untuk menjalankan 100 request secara serentak
if __name__ == "__main__":
    print("Memulai serangan 100 request ke API...")
    start_time = time.time()
    
    # Menggunakan ThreadPool untuk menjalankan banyak proses bersamaan
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        for i in range(1, 101):
            executor.submit(send_quiz, i)
            
    end_time = time.time()
    print(f"\nSelesai mengirim 100 kuis dalam waktu {end_time - start_time:.2f} detik!")