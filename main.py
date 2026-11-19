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

def create_clip():
    raw_file = "raw.mp4"
    final_file = "final_short.mp4"

    for f in [raw_file, final_file]:
        if os.path.exists(f):
            os.remove(f)

    cookie_args = []
    if os.path.exists("cookies.txt") and os.path.getsize("cookies.txt") > 0:
        cookie_args = ["--cookies", "cookies.txt"]

    print("🔍 Latest GTA 6 gameplay clip dhundh raha hai...")
    title_cmd = ["yt-dlp", *cookie_args, "--get-title", "ytsearch1:GTA 6 gameplay clip"]
    source_title = subprocess.check_output(title_cmd, text=True).strip()

    yt_cmd = [
        "yt-dlp",
        *cookie_args,
        "ytsearch1:GTA 6 gameplay clip",
        "-f", "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]",
        "--download-sections", "*0:10-0:40",
        "-o", raw_file
    ]
    subprocess.run(yt_cmd, check=True)

    print("✂️ Video ko 9:16 Vertical (Shorts/Reels) me crop kar raha hai...")
    ffmpeg_cmd = [
        "ffmpeg", "-y", "-i", raw_file,
        "-vf", "crop=ih*9/16:ih,scale=1080:1920",
        "-c:v", "libx264", "-preset", "fast", "-c:a", "aac",
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
