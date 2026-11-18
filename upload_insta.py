import os
from instagrapi import Client

def upload_reel(file_path, caption):
    if not os.path.exists(file_path):
        print(f"❌ Error: '{file_path}' nahi mili!")
        return

    cl = Client()
    session_file = "insta_session.json"

    if os.path.exists(session_file):
        cl.load_settings(session_file)
        print("🔄 Saved session load ho gaya...")
    else:
        print("🔐 Browser Session ID se login ho raha hai...")
        cl.login_by_sessionid("YOUR_SESSION_ID")
        cl.dump_settings(session_file)
        print("✅ Login successful! insta_session.json ban gaya!")

    print(f"🚀 Uploading '{file_path}' as Reel...")
    media = cl.clip_upload(file_path, caption)
    print(f"✅ Reel Uploaded! Media ID: {media.pk}")

if __name__ == "__main__":
    upload_reel(
        file_path="test.mp4",
        caption="GTA 6 Crazy Moment! 🔥🎮 #gta6 #gaming #reels"
    )