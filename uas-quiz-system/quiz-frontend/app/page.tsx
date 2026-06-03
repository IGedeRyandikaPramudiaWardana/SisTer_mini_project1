"use client";
import { useState } from "react";

export default function Home() {
  const [studentId, setStudentId] = useState("");
  const [answers, setAnswers] = useState({
    soal_1: "", soal_2: "", soal_3: "", soal_4: "", soal_5: ""
  });
  
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  
  // State untuk menampung hasil
  const [finalScore, setFinalScore] = useState<number | null>(null);
  const [resultDetails, setResultDetails] = useState<any>(null);

  const handleAnswerChange = (soalKey: string, value: string) => {
    setAnswers((prev) => ({ ...prev, [soalKey]: value }));
  };

  // Fungsi Polling: Mengecek nilai ke server setiap 1 detik
  // Fungsi Polling: Mengecek nilai ke server setiap 1 detik
  const pollResult = async (submissionId: number) => {
    try {
      const res = await fetch(`/api/result/${submissionId}?t=${Date.now()}`, {
        cache: "no-store", 
        headers: {
          "Pragma": "no-cache",
          "Cache-Control": "no-cache"
        }
      });

      // --- PROTEKSI BARU ---
      // Cek apakah balasan server benar-benar JSON. Jika bukan (misal HTML 404), skip dan coba lagi.
      const contentType = res.headers.get("content-type");
      if (!contentType || !contentType.includes("application/json")) {
        console.warn("Server belum siap / mengembalikan HTML. Mencoba lagi...");
        setTimeout(() => pollResult(submissionId), 1500);
        return;
      }
      // ---------------------

      const data = await res.json();

      if (res.ok && data.status === 'graded') {
        setFinalScore(data.score);
        setResultDetails(data.details);
        setLoading(false); // Matikan efek loading
        setMessage("✅ Nilai berhasil keluar!");
      } else {
        // Jika status masih 'pending' atau error sementara, ulangi cek 1 detik lagi
        setTimeout(() => pollResult(submissionId), 1000);
      }
    } catch (e) {
      console.error("Koneksi gagal, mencoba ulang:", e);
      // Jika internet putus sesaat, jangan crash, coba lagi 2 detik kemudian
      setTimeout(() => pollResult(submissionId), 2000);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setMessage("Sedang mengirim dan mengoreksi jawaban...");
    setFinalScore(null);
    setResultDetails(null);

    try {
      const response = await fetch("/api/submit", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ student_id: studentId, answers: answers }),
      });

      const data = await response.json();

      if (response.ok) {
        // Jawaban diterima! Sekarang mulai cek nilainya (Polling)
        pollResult(data.submission_id);
      } else {
        setMessage(`❌ Gagal: ${data.error}`);
        setLoading(false);
      }
    } catch (error) {
      setMessage("❌ Kesalahan jaringan.");
      setLoading(false);
    }
  };

  // Fungsi bantu untuk mewarnai kotak input (Hijau jika benar, Merah jika salah)
  const getInputColor = (soalKey: string) => {
    if (!resultDetails) return "border-gray-300 bg-white";
    return resultDetails[soalKey] 
      ? "border-green-500 bg-green-50 text-green-700 font-bold" 
      : "border-red-500 bg-red-50 text-red-700 font-bold";
  };

  return (
    <main className="min-h-screen bg-gray-100 flex items-center justify-center p-4">
      <div className="bg-white rounded-xl shadow-lg p-8 max-w-md w-full border-t-4 border-blue-600">
        <h1 className="text-2xl font-bold text-gray-800 mb-6 text-center">Portal Ujian Matematika</h1>

        {/* TAMPILAN SKOR AKHIR */}
        {finalScore !== null && (
          <div className="mb-6 bg-blue-900 text-white p-4 rounded-lg text-center animate-bounce">
            <p className="text-sm uppercase tracking-wide opacity-80">Skor Akhir Anda</p>
            <p className="text-5xl font-extrabold">{finalScore} / 100</p>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">ID Mahasiswa</label>
            <input
              type="text" required placeholder="MHS-001" value={studentId} readOnly={loading}
              onChange={(e) => setStudentId(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg outline-none text-black bg-gray-50"
            />
          </div>

          <div className="bg-blue-50 p-4 rounded-lg border border-blue-200 space-y-3">
            <h2 className="text-sm font-bold text-blue-800 mb-3 uppercase">Jawab Soal Berikut:</h2>
            
            <div className="flex items-center justify-between">
              <span className="font-semibold text-gray-800">1. 1 + 3 =</span>
              <input type="number" required value={answers.soal_1} readOnly={loading || finalScore !== null} onChange={(e) => handleAnswerChange("soal_1", e.target.value)} className={`w-20 px-3 py-1 border rounded text-center outline-none ${getInputColor("soal_1")}`} />
            </div>
            <div className="flex items-center justify-between">
              <span className="font-semibold text-gray-800">2. 2 + 5 =</span>
              <input type="number" required value={answers.soal_2} readOnly={loading || finalScore !== null} onChange={(e) => handleAnswerChange("soal_2", e.target.value)} className={`w-20 px-3 py-1 border rounded text-center outline-none ${getInputColor("soal_2")}`} />
            </div>
            <div className="flex items-center justify-between">
              <span className="font-semibold text-gray-800">3. 4 - 1 =</span>
              <input type="number" required value={answers.soal_3} readOnly={loading || finalScore !== null} onChange={(e) => handleAnswerChange("soal_3", e.target.value)} className={`w-20 px-3 py-1 border rounded text-center outline-none ${getInputColor("soal_3")}`} />
            </div>
            <div className="flex items-center justify-between">
              <span className="font-semibold text-gray-800">4. 7 - 2 =</span>
              <input type="number" required value={answers.soal_4} readOnly={loading || finalScore !== null} onChange={(e) => handleAnswerChange("soal_4", e.target.value)} className={`w-20 px-3 py-1 border rounded text-center outline-none ${getInputColor("soal_4")}`} />
            </div>
            <div className="flex items-center justify-between">
              <span className="font-semibold text-gray-800">5. 1 + 1 =</span>
              <input type="number" required value={answers.soal_5} readOnly={loading || finalScore !== null} onChange={(e) => handleAnswerChange("soal_5", e.target.value)} className={`w-20 px-3 py-1 border rounded text-center outline-none ${getInputColor("soal_5")}`} />
            </div>
          </div>

          <button type="submit" disabled={loading || finalScore !== null}
            className={`w-full py-2.5 rounded-lg text-white font-semibold transition shadow-sm ${
              loading || finalScore !== null ? "bg-slate-400 cursor-not-allowed" : "bg-blue-600 hover:bg-blue-700"
            }`}
          >
            {loading ? "Mengkoreksi Jawaban... ⏳" : (finalScore !== null ? "Ujian Selesai" : "Kumpulkan Jawaban")}
          </button>
        </form>

        {message && (
          <div className={`mt-4 p-3 rounded-lg text-sm text-center font-medium ${message.includes("✅") ? "text-green-600" : "text-blue-600 animate-pulse"}`}>
            {message}
          </div>
        )}
      </div>
    </main>
  );
}