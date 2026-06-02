import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        // Setiap request dari Next.js ke /api/submit 
        // akan diteruskan diam-diam ke Nginx kita di port 8080
        source: '/api/submit',
        destination: 'http://localhost:8080/submit',
      },
    ]
  },
};

export default nextConfig;