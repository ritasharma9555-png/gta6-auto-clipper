import os
import subprocess

def process_gta_clips():
    print("GTA 6 Auto-Clipper Pipeline Started...")
    
    # Test ke liye ek sample video link (Aage ise live YouTube stream ya playlist se connect kar lenge)
    video_url = "https://www.youtube.com/watch?v=QdBZY2fkU-0"
    
    print(f"Downloading video: {video_url}")
    # yt-dlp se best quality video download karne ki command
    download_cmd = f"yt-dlp -f best -o 'input_video.mp4' {video_url}"
    subprocess.run(download_cmd, shell=True)
    
    print("Video downloaded! Now cutting into 9:16 short clip using FFmpeg...")
    
    # FFmpeg command: 5th second se 20th second tak ka clip cut karega (As a test)
    # 9:16 vertical crop aur cutting logic yahan add ho raha hai
    clip_cmd = "ffmpeg -i input_video.mp4 -ss 00:00:05 -to 00:00:20 -c:v copy -c:a copy output_short.mp4"
    subprocess.run(clip_cmd, shell=True)
    
    print("Short clip generated successfully: output_short.mp4!")

if __name__ == "__main__":
    process_gta_clips()
