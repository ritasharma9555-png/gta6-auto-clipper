import os
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

def upload_video(file_path, title, description, tags, privacy="private"):
    if not os.path.exists("token.json"):
        print("❌ Error: token.json nahi mili!")
        return

    if not os.path.exists(file_path):
        print(f"❌ Error: Video file '{file_path}' nahi mili!")
        return

    creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    youtube = build("youtube", "v3", credentials=creds)

    request_body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": "20"  # 20 = Gaming category
        },
        "status": {
            "privacyStatus": privacy,  # Testing ke liye 'private' rakha hai
            "selfDeclaredMadeForKids": False
        }
    }

    media = MediaFileUpload(file_path, chunksize=-1, resumable=True)

    print(f"🚀 Uploading '{file_path}' to YouTube...")
    request = youtube.videos().insert(
        part="snippet,status",
        body=request_body,
        media_body=media
    )

    response = request.execute()
    print(f"✅ Upload Successful! Video ID: {response['id']}")
    print(f"🔗 Link: https://youtube.com/shorts/{response['id']}")

if __name__ == "__main__":
    # Test upload details
    upload_video(
        file_path="test.mp4",
        title="GTA 6 Crazy Moment! 🔥 #Shorts #GTA6",
        description="Automated test clip for GTA 6! #gta6 #gaming #shorts",
        tags=["GTA 6", "GTA VI", "Gaming", "Shorts"],
        privacy="private"  # Baad me isko 'public' kar denge
    )