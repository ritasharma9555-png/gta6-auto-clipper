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

def download_recorded_clip(base_cmd, query, raw_file):
    search_target = f"ytsearch3:{query}"

    title_cmd = [*base_cmd, "--no-playlist", "--get-title", search_target]
    titles = [line.strip() for line in subprocess.check_output(title_cmd, text=True).splitlines() if line.strip()]
    source_title = titles[0] if titles else query

    yt_cmd = [
        *base_cmd,
        "--no-playlist",
        "--match-filter", "!is_live & duration > 60",
        "--max-downloads", "1",
        "--download-sections", "*0:15-0:45",
        search_target,
        "-f", "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=1080]+bestaudio/best[ext=mp4]/best",
        "--merge-output-format", "mp4",
        "-o", raw_file
    ]
    subprocess.run(yt_cmd, check=False, timeout=120)
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

    queries = ["IShowSpeed GTA 6 gameplay", "GTA 6 gameplay"]
    source_title = None

    for q in queries:
        try:
            print(f"🔍 '{q}' se recorded video clip nikal raha hai...")
            for f in [raw_file, final_file]:
                if os.path.exists(f):
                    os.remove(f)

            source_title = download_recorded_clip(base_cmd, q, raw_file)
            if not os.path.exists(raw_file) or os.path.getsize(raw_file) == 0:
                continue

            print("✂️ 9:16 Vertical (Shorts/Reels) me fast crop kar raha hai...")
            vf_filter = "crop=ih*9/16:ih,scale=1080:1920:flags=lanczos"

            if has_audio_stream(raw_file):
                ffmpeg_cmd = [
                    "ffmpeg", "-y",
                    "-i", raw_file,
                    "-vf", vf_filter,
                    "-c:v", "libx264", "-crf", "20", "-preset", "veryfast",
                    "-c:a", "aac", "-b:a", "192k",
                    "-movflags", "+faststart",
                    final_file
                ]
            else:
                ffmpeg_cmd = [
                    "ffmpeg", "-y",
                    "-i", raw_file,
                    "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
                    "-vf", vf_filter,
                    "-c:v", "libx264", "-crf", "20", "-preset", "veryfast",
                    "-c:a", "aac", "-b:a", "192k",
                    "-shortest",
                    "-movflags", "+faststart",
                    final_file
                ]

            subprocess.run(ffmpeg_cmd, check=True, timeout=120)
            if os.path.exists(final_file) and os.path.getsize(final_file) > 0:
                break
        except Exception as e:
            print(f"⚠️ '{q}' par issue aaya ({e}), next query try kar raha hai...")

    if not source_title or not os.path.exists(final_file) or os.path.getsize(final_file) == 0:
        raise RuntimeError("Recorded video se clip nahi ban paya.")

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
