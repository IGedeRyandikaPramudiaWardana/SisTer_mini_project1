import time
import random

class WorkerNode:
    def __init__(self, node_id):
        self.node_id = node_id
        self.next_node = None       # Menunjuk ke node sebelahnya
        self.is_leader = False
        self.participant = False    # Status apakah sedang ikut pemilu

    def set_next(self, next_node):
        self.next_node = next_node

    def receive_message(self, message_id):
        print(f"[Worker {self.node_id}] Menerima operan ID: {message_id}")
        time.sleep(1) # Jeda 1 detik agar prosesnya terlihat jelas di terminal

        # Jika ID yang diterima lebih BESAR dari ID sendiri -> Teruskan pesan itu
        if message_id > self.node_id:
            self.participant = True
            print(f"  -> {message_id} lebih besar dari {self.node_id}. Meneruskan ke Worker {self.next_node.node_id}...")
            self.next_node.receive_message(message_id)
            
        # Jika ID yang diterima lebih KECIL -> Ganti dengan ID sendiri, lalu teruskan
        elif message_id < self.node_id and not self.participant:
            self.participant = True
            print(f"  -> {message_id} lebih kecil. Worker {self.node_id} mengganti pesan dengan ID-nya sendiri!")
            self.next_node.receive_message(self.node_id)
            
        # Jika ID yang diterima SAMA dengan ID sendiri -> SAH MENJADI LEADER!
        elif message_id == self.node_id:
            self.is_leader = True
            self.participant = False
            print(f"\n🌟 [Worker {self.node_id}] SAYA ADALAH LEADER BARU! 🌟\n")
            # Beritahu semua anggota lingkaran
            self.next_node.announce_leader(self.node_id)

    def announce_leader(self, leader_id):
        if not self.is_leader:
            print(f"[Worker {self.node_id}] Mengakui dan tunduk pada Worker {leader_id} sebagai Leader.")
            self.next_node.announce_leader(leader_id)

    def start_election(self):
        print(f"\n--- Worker {self.node_id} Memulai Pemilihan Leader ---")
        self.participant = True
        self.next_node.receive_message(self.node_id)


if __name__ == "__main__":
    print("Membangun jaringan Ring (Lingkaran) dengan 5 Worker...\n")
    
    # Membuat 5 node dengan ID acak antara 100 - 999
    nodes = [WorkerNode(random.randint(100, 999)) for _ in range(5)]
    
    # Menghubungkan node agar melingkar (0->1, 1->2, 2->3, 3->4, 4->0)
    for i in range(5):
        nodes[i].set_next(nodes[(i + 1) % 5])
        print(f"Worker {nodes[i].node_id} -> menunjuk ke -> Worker {nodes[(i + 1) % 5].node_id}")
    
    time.sleep(2)
    
    # Mensimulasikan salah satu node (misalnya node indeks ke-0) memulai pemilihan
    nodes[0].start_election()