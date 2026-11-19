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

def get_media_duration(filepath):
    probe = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            filepath
        ],
        capture_output=True,
        text=True
    )
    try:
        return float(probe.stdout.strip())
    except (ValueError, TypeError):
        return 0.0

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

def download_from_query(base_cmd, query, raw_file):
    title_cmd = [*base_cmd, "--no-playlist", "--get-title", f"ytsearch1:{query}"]
    source_title = subprocess.check_output(title_cmd, text=True).strip()

    yt_cmd = [
        *base_cmd,
        "--no-playlist",
        "--concurrent-fragments", "1",
        f"ytsearch1:{query}",
        "-f", "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=1080]+bestaudio/best[ext=mp4]/best",
        "--merge-output-format", "mp4",
        "-o", raw_file
    ]
    subprocess.run(yt_cmd, check=True)
    return source_title

def create_clip():
    raw_file = "raw.mp4"
    final_file = "final_short.mp4"

    for f in [raw_file, final_file]:
        if os.path.exists(f):
            os.remove(f)

    base_cmd = ["yt-dlp", "--js-runtimes", "node", "--remote-components", "ejs:github"]
    if os.path.exists("cookies.txt") and os.path.getsize("cookies.txt") > 0:
        base_cmd += ["--cookies", "cookies.txt"]

    queries = ["IShowSpeed GTA 6", "GTA 6 gameplay clip"]
    source_title = None

    for q in queries:
        try:
            print(f"🔍 '{q}' ke liye clip dhundh aur download kar raha hai...")
            for f in [raw_file, final_file]:
                if os.path.exists(f):
                    os.remove(f)
            source_title = download_from_query(base_cmd, q, raw_file)
            if not os.path.exists(raw_file) or os.path.getsize(raw_file) == 0:
                continue

            duration = get_media_duration(raw_file)
            start_time = "00:00:15" if duration > 25 else "00:00:00"
            vf_filter = "crop=ih*9/16:ih,scale=1080:1920:flags=lanczos"

            print(f"✂️ High quality 9:16 Vertical (start={start_time}) me crop kar raha hai...")
            if has_audio_stream(raw_file):
                ffmpeg_cmd = [
                    "ffmpeg", "-y", "-ss", start_time, "-t", "30",
                    "-i", raw_file,
                    "-vf", vf_filter,
                    "-c:v", "libx264", "-crf", "18", "-preset", "medium",
                    "-c:a", "aac", "-b:a", "192k",
                    "-movflags", "+faststart",
                    final_file
                ]
            else:
                ffmpeg_cmd = [
                    "ffmpeg", "-y", "-ss", start_time, "-t", "30",
                    "-i", raw_file,
                    "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
                    "-vf", vf_filter,
                    "-c:v", "libx264", "-crf", "18", "-preset", "medium",
                    "-c:a", "aac", "-b:a", "192k",
                    "-shortest",
                    "-movflags", "+faststart",
                    final_file
                ]

            subprocess.run(ffmpeg_cmd, check=True)
            if os.path.exists(final_file) and os.path.getsize(final_file) > 0:
                break
        except Exception as e:
            print(f"⚠️ '{q}' par issue aaya ({e}), next option try kar raha hai...")

    if not source_title or not os.path.exists(final_file) or os.path.getsize(final_file) == 0:
        raise RuntimeError("Kisi bhi query se valid clip generate nahi ho paya.")

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
