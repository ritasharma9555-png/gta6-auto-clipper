import json
import os
import subprocess
import urllib.request
from ai_brain import generate_metadata
from upload_youtube import upload_video
from upload_insta import upload_reel

NTFY_TOPIC = "haf_spidy"  # Apna unique ntfy topic naam yahan daal

def send_notification(title, message):
    try:
        req = urllib.request.Request(
            f"https://ntfy.sh/{NTFY_TOPIC}",
            data=message.encode("utf-8"),
            headers={"Title": title, "Tags": "fire,video_game"}
        )
        urllib.request.urlopen(req)
        print("🔔 Phone par notification bhej diya!")
    except Exception as e:
        print(f"⚠️ Notification error: {e}")

def has_audio_stream(filepath):
    probe = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-select_streams", "a",
            "-show_entries", "stream=index",
            "-of", "csv=p=0",
            filepath
        ],
        capture_output=True,
        text=True
    )
    return bool(probe.stdout.strip())

def format_sec(seconds):
    seconds = max(0, int(seconds))
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h}:{m:02d}:{s:02d}"

def find_hype_window(base_cmd, query):
    search_target = f"ytsearch5:{query}"
    cmd = [*base_cmd, "--no-playlist", "--dump-json", search_target]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=90)

    for line in proc.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            info = json.loads(line)
        except json.JSONDecodeError:
            continue

        if info.get("is_live"):
            continue

        duration = float(info.get("duration") or 0)
        if duration < 45:
            continue

        webpage_url = info.get("webpage_url") or info.get("url")
        title = info.get("title") or query
        if not webpage_url:
            continue

        heatmap = info.get("heatmap")
        if isinstance(heatmap, list) and len(heatmap) > 0:
            best_pt = max(heatmap, key=lambda x: float(x.get("value") or 0))
            peak_time = float(best_pt.get("start_time") or best_pt.get("end_time") or duration * 0.35)
            start_sec = max(0, int(peak_time - 5))
            end_sec = min(int(duration), start_sec + 30)
            if end_sec - start_sec >= 15:
                return webpage_url, title, start_sec, end_sec, f"Most Replayed peak @ {peak_time:.1f}s"

        start_sec = max(15, int(duration * 0.30))
        if start_sec + 30 > duration:
            start_sec = max(0, int(duration) - 30)
        end_sec = min(int(duration), start_sec + 30)
        return webpage_url, title, start_sec, end_sec, f"Mid-action window ({start_sec}s-{end_sec}s)"

    raise RuntimeError(f"'{query}' ke liye suitable recorded video nahi mila.")

def create_clip():
    raw_file = "raw.mp4"
    final_file = "final_short.mp4"

    for f in [raw_file, final_file]:
        if os.path.exists(f):
            os.remove(f)

    base_cmd = ["yt-dlp", "--js-runtimes", "node", "--remote-components", "ejs:github"]
    if os.path.exists("cookies.txt") and os.path.getsize("cookies.txt") > 0:
        base_cmd += ["--cookies", "cookies.txt"]

    queries = ["IShowSpeed GTA 6 gameplay", "GTA 6 gameplay"]
    source_title = None

    for q in queries:
        try:
            print(f"🔍 '{q}' me hyped/most-replayed scene dhundh raha hai...")
            for f in [raw_file, final_file]:
                if os.path.exists(f):
                    os.remove(f)

            video_url, source_title, start_sec, end_sec, reason = find_hype_window(base_cmd, q)
            sec_range = f"*{format_sec(start_sec)}-{format_sec(end_sec)}"
            print(f"🔥 Scene selected ({reason}): {source_title} [{sec_range}]")

            yt_cmd = [
                *base_cmd,
                "--no-playlist",
                "--concurrent-fragments", "1",
                "--download-sections", sec_range,
                video_url,
                "-f", "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=720]+bestaudio/best[ext=mp4]/best",
                "--merge-output-format", "mp4",
                "-o", raw_file
            ]
            subprocess.run(yt_cmd, check=True, timeout=150)

            if not os.path.exists(raw_file) or os.path.getsize(raw_file) == 0:
                continue

            print("✂️ Bina over-zoom ke 9:16 Vertical (Blurred BG + Full Frame) bana raha hai...")
            filter_complex = (
                "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,"
                "crop=1080:1920,boxblur=20:5,eq=brightness=-0.12[bg];"
                "[0:v]scale=1080:608:force_original_aspect_ratio=decrease[fg];"
                "[bg][fg]overlay=(W-w)/2:(H-h)/2,format=yuv420p[vout]"
            )

            if has_audio_stream(raw_file):
                ffmpeg_cmd = [
                    "ffmpeg", "-y",
                    "-i", raw_file,
                    "-filter_complex", filter_complex,
                    "-map", "[vout]", "-map", "0:a?",
                    "-c:v", "libx264", "-crf", "22", "-preset", "ultrafast",
                    "-c:a", "aac", "-b:a", "128k",
                    "-movflags", "+faststart",
                    final_file
                ]
            else:
                ffmpeg_cmd = [
                    "ffmpeg", "-y",
                    "-i", raw_file,
                    "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
                    "-filter_complex", filter_complex,
                    "-map", "[vout]", "-map", "1:a",
                    "-c:v", "libx264", "-crf", "22", "-preset", "ultrafast",
                    "-c:a", "aac", "-b:a", "128k",
                    "-shortest",
                    "-movflags", "+faststart",
                    final_file
                ]

            subprocess.run(ffmpeg_cmd, check=True, timeout=120)
            if os.path.exists(final_file) and os.path.getsize(final_file) > 10000:
                break
        except Exception as e:
            print(f"⚠️ '{q}' par issue aaya ({e}), next query try kar raha hai...")

    if not source_title or not os.path.exists(final_file) or os.path.getsize(final_file) <= 10000:
        raise RuntimeError("Hype scene clip nahi ban paya.")

    return final_file, source_title

if __name__ == "__main__":
    video, source_title = create_clip()

    print("🧠 AI Brain se viral Title aur Caption banwa raha hai...")
    meta = generate_metadata(source_title)

    # 1. YouTube Shorts par upload
    upload_video(
        video,
        title=meta["yt_title"],
        description=meta["insta_caption"],
        tags=meta["tags"],
        privacy="public"
    )

    # 2. Instagram Reels par upload
    upload_reel(video, caption=meta["insta_caption"])

    # 3. Phone par Notification bhej
    send_notification(
        "GTA 6 Bot Upload Done!",
        f"Title: {meta['yt_title']}\nYouTube Shorts + Instagram Reels dono live ho gaye!"
    )
    print("🎉 Mission Complete!")
