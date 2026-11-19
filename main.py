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

def download_from_query(base_cmd, query, raw_file):
    title_cmd = [*base_cmd, "--no-playlist", "--get-title", f"ytsearch1:{query}"]
    source_title = subprocess.check_output(title_cmd, text=True).strip()

    yt_cmd = [
        *base_cmd,
        "--no-playlist",
        f"ytsearch1:{query}",
        "-f", "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=1080]+bestaudio/best[ext=mp4]/best",
        "--merge-output-format", "mp4",
        "--download-sections", "*0:15-0:45",
        "--force-keyframes-at-cuts",
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
            if os.path.exists(raw_file):
                os.remove(raw_file)
            source_title = download_from_query(base_cmd, q, raw_file)
            if os.path.exists(raw_file) and os.path.getsize(raw_file) > 0:
                break
        except Exception as e:
            print(f"⚠️ '{q}' par issue aaya ({e}), next option try kar raha hai...")

    if not source_title or not os.path.exists(raw_file):
        raise RuntimeError("Kisi bhi query se video download nahi ho paya.")

    print("✂️ High quality 9:16 Vertical (Shorts/Reels) me crop kar raha hai...")
    ffmpeg_cmd = [
        "ffmpeg", "-y", "-i", raw_file,
        "-vf", "crop=ih*9/16:ih,scale=1080:1920:flags=lanczos",
        "-c:v", "libx264", "-crf", "18", "-preset", "medium",
        "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart",
        final_file
    ]
    subprocess.run(ffmpeg_cmd, check=True)
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
