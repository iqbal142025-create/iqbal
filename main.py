#!/usr/bin/env python3
"""Simple vertical TikTok motion-graphics generator."""
import argparse, json, math, os, shutil, subprocess, sys, tempfile
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import textwrap

def font(size, bold=False):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
    ]
    for p in candidates:
        if os.path.exists(p): return ImageFont.truetype(p, size)
    return ImageFont.load_default()

def wrap_text(draw, text, fnt, max_width):
    words, lines, line = text.split(), [], ""
    for word in words:
        test = (line + " " + word).strip()
        if draw.textbbox((0,0), test, font=fnt)[2] <= max_width: line = test
        else:
            if line: lines.append(line)
            line = word
    if line: lines.append(line)
    return lines

def draw_frame(w, h, scene, t, total, index):
    y, x = np.mgrid[0:h, 0:w]
    pulse = 0.5 + 0.5 * math.sin(t * 0.7 + index)
    glow_x = int(w * (0.25 + 0.5 * (0.5 + 0.5 * math.sin(t * 0.22))))
    glow_y = int(h * (0.32 + 0.12 * math.cos(t * 0.3)))
    dist = np.sqrt(((x-glow_x)/w)**2 + ((y-glow_y)/h)**2)
    glow = np.clip(1 - dist * 1.7, 0, 1)
    arr = np.zeros((h,w,3), dtype=np.uint8)
    arr[:,:,0] = np.clip(8 + glow*22 + pulse*4,0,255)
    arr[:,:,1] = np.clip(13 + glow*20,0,255)
    arr[:,:,2] = np.clip(30 + glow*55 + pulse*8,0,255)
    im = Image.fromarray(arr, "RGB")
    d = ImageDraw.Draw(im, "RGBA")
    # subtle moving particles
    for k in range(34):
        px = int((k*173 + t*(12+k%5)*5) % w)
        py = int((k*293 + math.sin(t*.45+k)*34) % h)
        r = 2 + (k%3)
        d.ellipse((px-r,py-r,px+r,py+r), fill=(120,190,255,35))
    # central translucent panel
    panel=(w*.08,h*.27,w*.92,h*.73)
    d.rounded_rectangle(panel, radius=42, fill=(3,8,20,105), outline=(130,190,255,55), width=2)
    title = scene.get("title","").upper()
    subtitle = scene.get("subtitle","")
    tf, sf = font(max(42,int(w*.085)),True), font(max(26,int(w*.042)))
    title_lines=wrap_text(d,title,tf,int(w*.72))
    line_h=int(tf.size*1.2)
    block_h=len(title_lines)*line_h
    start_y=int(h*.5-block_h*.55)
    # subtle entrance
    alpha=int(210+45*min(1,t/.7))
    for j,line in enumerate(title_lines):
        bb=d.textbbox((0,0),line,font=tf,stroke_width=2)
        tw=bb[2]-bb[0]
        d.text(((w-tw)//2,start_y+j*line_h),line,font=tf,fill=(245,248,255,alpha),stroke_width=2,stroke_fill=(10,20,45,180))
    sub_lines=wrap_text(d,subtitle,sf,int(w*.72))
    sy=int(h*.62)
    for j,line in enumerate(sub_lines):
        tw=d.textbbox((0,0),line,font=sf)[2]
        d.text(((w-tw)//2,sy+j*int(sf.size*1.4)),line,font=sf,fill=(170,210,255,235))
    # progress line
    d.rounded_rectangle((w*.12,h*.88,w*.88,h*.885),radius=5,fill=(255,255,255,45))
    p=max(0,min(1,(index + t/max(.01,scene["duration"]))/total))
    d.rounded_rectangle((w*.12,h*.88,w*(.12+.76*p),h*.885),radius=5,fill=(90,180,255,220))
    return im

def srt_time(seconds):
    ms=int(round(seconds*1000)); hh=ms//3600000; ms%=3600000
    mm=ms//60000; ms%=60000; ss=ms//1000; ms%=1000
    return f"{hh:02}:{mm:02}:{ss:02},{ms:03}"

async def make_voice(text, voice, path):
    import edge_tts
    await edge_tts.Communicate(text=text, voice=voice, rate="+0%", volume="+0%").save(str(path))

def main():
    ap=argparse.ArgumentParser(description="Buat video TikTok 9:16 dari naskah JSON")
    ap.add_argument("--script",default="contoh.json")
    ap.add_argument("--output",default="hasil.mp4")
    ap.add_argument("--no-voice",action="store_true")
    args=ap.parse_args()
    if not shutil.which("ffmpeg"):
        sys.exit("FFmpeg tidak ditemukan. Install FFmpeg lalu tambahkan ke PATH.")
    data=json.loads(Path(args.script).read_text(encoding="utf-8"))
    scenes=data["scenes"]; w=int(data.get("width",1080)); h=int(data.get("height",1920)); fps=int(data.get("fps",30))
    if w%2 or h%2: sys.exit("Lebar dan tinggi harus bilangan genap untuk encoding H.264.")
    total=sum(float(s["duration"]) for s in scenes)
    out=Path(args.output); out.parent.mkdir(parents=True,exist_ok=True)
    srt_path=out.with_suffix(".srt")
    cursor=0; srt=[]
    for i,s in enumerate(scenes,1):
        srt.append(f"{i}\n{srt_time(cursor)} --> {srt_time(cursor+float(s['duration']))}\n{s.get('subtitle','')}\n")
        cursor+=float(s["duration"])
    srt_path.write_text("\n".join(srt),encoding="utf-8")
    voice_path=out.with_suffix(".mp3")
    has_voice=False
    narration=" ".join(s.get("narration","") for s in scenes).strip()
    if not args.no_voice and narration:
        try:
            import asyncio
            asyncio.run(make_voice(narration,data.get("voice","id-ID-ArdiNeural"),voice_path))
            has_voice=True
        except Exception as e:
            print(f"Peringatan: narasi gagal dibuat ({e}). Video dibuat tanpa suara.")
    cmd=["ffmpeg","-y","-f","rawvideo","-vcodec","rawvideo","-pix_fmt","rgb24","-s",f"{w}x{h}","-r",str(fps),"-i","-","-an","-c:v","libx264","-pix_fmt","yuv420p","-preset","medium","-crf","20","-movflags","+faststart",str(out)]
    proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
    try:
        for idx,scene in enumerate(scenes):
            frames=int(float(scene["duration"])*fps)
            for f in range(frames):
                frame=draw_frame(w,h,scene,f/fps,total,idx)
                proc.stdin.write(np.asarray(frame,dtype=np.uint8).tobytes())
        proc.stdin.close()
        code=proc.wait()
        if code: sys.exit(f"FFmpeg gagal dengan kode {code}")
    except BrokenPipeError:
        proc.wait(); sys.exit("FFmpeg berhenti sebelum proses selesai.")
    if has_voice:
        mux=out.with_name(out.stem+"_with_voice.mp4")
        subprocess.run(["ffmpeg","-y","-i",str(out),"-i",str(voice_path),"-c:v","copy","-c:a","aac","-shortest","-movflags","+faststart",str(mux)],check=True)
        mux.replace(out)
        voice_path.unlink(missing_ok=True)
    print(f"Video selesai: {out.resolve()}")
    print(f"Subtitle selesai: {srt_path.resolve()}")
    print(f"Caption: {data.get('caption','')}")

if __name__=="__main__": main()
