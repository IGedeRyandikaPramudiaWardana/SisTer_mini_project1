# Menggunakan Python versi ringan
FROM python:3.13-slim

# Mencegah Python menahan output log (Matikan Buffering)
ENV PYTHONUNBUFFERED=1

# Menentukan direktori kerja di dalam container
WORKDIR /app

# Meng-copy semua file dari komputer ke dalam container
COPY . /app

# Menginstal library yang dibutuhkan
RUN pip install Flask Flask-SQLAlchemy pika requests

# Mengekspos port 5000 (untuk API) dan 8000 (untuk RPC)
EXPOSE 5000 8000