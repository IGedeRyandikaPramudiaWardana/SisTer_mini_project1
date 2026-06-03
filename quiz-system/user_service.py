from xmlrpc.server import SimpleXMLRPCServer
from socketserver import ThreadingMixIn # <-- Library tambahan untuk Multi-Thread

# Membuat kelas server baru yang punya banyak "kasir" (Thread)
class ThreadedXMLRPCServer(ThreadingMixIn, SimpleXMLRPCServer):
    pass

VALID_STUDENTS = {
    "MHS-001": "Budi Santoso",
    "MHS-002": "Siti Aminah",
    "MHS-003": "Andi Wijaya"
}

def verify_student(student_id):
    if student_id in VALID_STUDENTS:
        return True
    return False

if __name__ == "__main__":
    # Menggunakan server Multi-Thread yang baru dibuat
    server = ThreadedXMLRPCServer(("0.0.0.0", 8000), allow_none=True)
    print("🚀 Server RPC (User Service) Multi-Thread berjalan di port 8000...")
    
    server.register_function(verify_student, "verify_student")
    server.serve_forever()