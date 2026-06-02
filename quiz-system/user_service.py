from xmlrpc.server import SimpleXMLRPCServer

# Database tiruan (mock) berisi daftar mahasiswa yang terdaftar
VALID_STUDENTS = {
    "MHS-001": "Budi Santoso",
    "MHS-002": "Siti Aminah",
    "MHS-003": "Andi Wijaya"
}

# Fungsi yang akan dipanggil dari jarak jauh (oleh app.py)
def verify_student(student_id):
    print(f"[RPC Server] Menerima permintaan verifikasi untuk ID: {student_id}")
    if student_id in VALID_STUDENTS:
        print(f"[RPC Server] -> Valiad! Itu adalah {VALID_STUDENTS[student_id]}")
        return True
    else:
        print("[RPC Server] -> Tidak Valid/Tidak Terdaftar!")
        return False

# Memulai server RPC di port 8000
if __name__ == "__main__":
    server = SimpleXMLRPCServer(("0.0.0.0", 8000))
    print("Server RPC (User Service) berjalan di port 8000...")
    
    # Mendaftarkan fungsi verify_student agar bisa diakses layanan lain
    server.register_function(verify_student, "verify_student")
    
    # Menjalankan server terus-menerus
    server.serve_forever()
    
    print("Server RPC (User Service) telah berhenti.")