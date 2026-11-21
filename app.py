import json
import subprocess
import sys
import tempfile
from pathlib import Path
import streamlit as st

ROOT = Path(__file__).parent
st.set_page_config(page_title="TikTok Automation", page_icon="🎬", layout="centered")
st.title("🎬 TikTok Automation")
st.caption("Ubah ide dan naskah menjadi video vertikal 9:16.")

DEFAULT = {
  "title": "Perang Terbesar Adalah Melawan Diri Sendiri",
  "caption": "Kemenangan terbesar adalah mengalahkan diri sendiri. #Motivasi #RefleksiDiri",
  "voice": "id-ID-ArdiNeural",
  "width": 1080, "height": 1920, "fps": 30,
  "scenes": [
    {"duration": 5, "title": "PERANG TERBESAR", "subtitle": "Bukan melawan dunia...", "narration": "Perang terbesar dalam hidup bukanlah melawan dunia."},
    {"duration": 6, "title": "TAPI DIRI SENDIRI", "subtitle": "Melawan rasa takut dan ragu.", "narration": "Tetapi melawan diri sendiri, rasa takut, dan keraguan."},
    {"duration": 7, "title": "MULAI MELANGKAH", "subtitle": "Tidak harus sempurna untuk memulai.", "narration": "Kamu tidak harus sempurna. Mulailah dengan satu langkah kecil."},
    {"duration": 6, "title": "JADI LEBIH BAIK", "subtitle": "Menanglah atas dirimu yang kemarin.", "narration": "Kemenangan sejati adalah menjadi lebih baik dari dirimu yang kemarin."}
  ]
}
with st.expander("Panduan singkat", expanded=False):
    st.write("Isi naskah dalam format JSON. Setiap adegan memerlukan durasi (detik), judul, subtitle, dan narasi. FFmpeg harus terpasang di komputer.")
raw = st.text_area("Naskah video (JSON)", value=json.dumps(DEFAULT, ensure_ascii=False, indent=2), height=430)
voice = st.checkbox("Buat narasi suara bahasa Indonesia", value=True)
if st.button("🚀 Buat video", type="primary", use_container_width=True):
    try:
        data = json.loads(raw)
        if not isinstance(data.get("scenes"), list) or not data["scenes"]:
            raise ValueError("Tambahkan minimal satu adegan pada scenes.")
        for i, scene in enumerate(data["scenes"], 1):
            if float(scene.get("duration", 0)) <= 0:
                raise ValueError(f"Durasi adegan {i} harus lebih dari 0.")
            for key in ("title", "subtitle", "narration"):
                if key not in scene:
                    raise ValueError(f"Adegan {i} belum memiliki kolom {key}.")
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            script_path = tmp / "script.json"
            output_path = tmp / "video_tiktok.mp4"
            script_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            command = [sys.executable, str(ROOT / "main.py"), "--script", str(script_path), "--output", str(output_path)]
            if not voice:
                command.append("--no-voice")
            with st.spinner("Sedang membuat video. Proses dapat memerlukan beberapa menit..."):
                result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
            if result.returncode != 0:
                st.error("Video belum berhasil dibuat.")
                st.code(result.stderr or result.stdout)
            elif output_path.exists():
                video_bytes = output_path.read_bytes()
                st.success("Video berhasil dibuat!")
                st.video(video_bytes)
                st.download_button("⬇️ Unduh video MP4", video_bytes, file_name="video_tiktok.mp4", mime="video/mp4", use_container_width=True)
                subtitle_path = output_path.with_suffix(".srt")
                if subtitle_path.exists():
                    st.download_button("Unduh subtitle SRT", subtitle_path.read_bytes(), file_name="subtitle_tiktok.srt", mime="text/plain")
                st.info(data.get("caption", "Tambahkan caption sebelum mengunggah."))
            else:
                st.error(result.stdout or "File video tidak ditemukan.")
    except json.JSONDecodeError as exc:
        st.error(f"Format JSON tidak valid: {exc}")
    except Exception as exc:
        st.error(str(exc))
