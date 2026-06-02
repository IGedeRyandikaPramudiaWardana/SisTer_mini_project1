"use client";

import { useState } from "react";

export default function Home() {
  const [studentId, setStudentId] = useState("");
  const [answers, setAnswers] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setMessage("");

    try {
      // Mengirim data ke jalur proxy yang sudah kita buat di next.config.mjs
      const response = await fetch("/api/submit", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          student_id: studentId,
          answers: answers,
        }),
      });

      const data = await response.json();

      if (response.ok) {
        setMessage(`✅ Sukses: ${data.message} (ID: ${data.submission_id})`);
        setStudentId("");
        setAnswers("");
      } else {
        setMessage(`❌ Gagal: ${data.error}`);
      }
    } catch (error) {
      setMessage("❌ Terjadi kesalahan jaringan saat menghubungi server.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-gray-100 flex items-center justify-center p-4">
      <div className="bg-white rounded-xl shadow-lg p-8 max-w-md w-full">
        <h1 className="text-2xl font-bold text-gray-800 mb-6 text-center">
          Portal Ujian Terdistribusi
        </h1>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              ID Mahasiswa
            </label>
            <input
              type="text"
              required
              placeholder="Contoh: MHS-001"
              value={studentId}
              onChange={(e) => setStudentId(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition text-black"
            />
            <p className="text-xs text-gray-500 mt-1">ID Valid: MHS-001, MHS-002, MHS-003</p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Jawaban Ujian
            </label>
            <textarea
              required
              rows={4}
              placeholder="Tuliskan jawaban lengkapmu di sini..."
              value={answers}
              onChange={(e) => setAnswers(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition text-black resize-none"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className={`w-full py-2.5 rounded-lg text-white font-semibold transition ${
              loading ? "bg-blue-300 cursor-not-allowed" : "bg-blue-600 hover:bg-blue-700"
            }`}
          >
            {loading ? "Memproses..." : "Kumpulkan Jawaban"}
          </button>
        </form>

        {message && (
          <div className={`mt-6 p-4 rounded-lg text-sm ${
            message.includes("✅") ? "bg-green-50 text-green-800" : "bg-red-50 text-red-800"
          }`}>
            {message}
          </div>
        )}
      </div>
    </main>
  );
}