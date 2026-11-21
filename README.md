# TikTok Automation

Generator video TikTok vertikal 9:16 dari naskah JSON. Proyek ini membuat latar animasi sederhana, teks layar, subtitle SRT, narasi suara (opsional), dan MP4 menggunakan Python, Pillow, FFmpeg, dan Edge TTS.

## Fitur
- Format video 1080x1920 (9:16), default 30 FPS.
- Animasi latar gradien dan partikel sederhana.
- Teks utama dan subtitle per adegan.
- Narasi bahasa Indonesia dengan Edge TTS (opsional).
- Subtitle .srt dan metadata/caption untuk unggahan.

## Persiapan
1. Install Python 3.10+ dan FFmpeg.
2. Clone repository:
   `git clone https://github.com/iqbal142025-create/iqbal.git`
3. Install dependensi:
   `pip install -r requirements.txt`
4. Buat suara dan video:
   `python main.py --script contoh.json --output hasil.mp4`

Jika tidak ingin membuat narasi otomatis, gunakan `--no-voice`. Video tetap dibuat dan subtitle tetap tersedia.

## Mengubah konten
Edit `contoh.json`. Setiap adegan memiliki `duration`, `title`, `subtitle`, dan `narration`. Durasi total video mengikuti jumlah durasi adegan.

## Catatan
- Edge TTS membutuhkan koneksi internet untuk menghasilkan suara.
- FFmpeg harus tersedia pada PATH sistem.
- Generator ini membuat motion graphic sederhana; bukan generator animasi 3D penuh atau layanan posting otomatis.
- Periksa kembali hasil video, ejaan, hak cipta musik, dan subtitle sebelum mengunggah ke TikTok.
