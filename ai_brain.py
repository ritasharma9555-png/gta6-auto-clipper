import os
import json
from google import genai

def generate_metadata(source_title):
    api_key = os.environ.get("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)

    prompt = f"""
    You are a viral gaming Shorts/Reels creator for GTA 6.
    Original clip context/title: "{source_title}"

    Generate a JSON object with these exact keys (no markdown, just raw JSON):
    - "yt_title": Catchy, human-like YouTube Shorts title under 70 characters with 1-2 emojis and #Shorts #GTA6
    - "insta_caption": Short, engaging, casual Instagram Reel caption with 5 relevant hashtags
    - "hook": A 3-5 word punchy hook to put on screen (ALL CAPS)
    - "tags": A list of 5 SEO tags for YouTube
    """

    # Agar ek model busy (503) ho toh agla try karega
    models = ["gemini-3.8-flash", "gemini-3.7-flash", "gemini-3.5-flash"]
    
    for m in models:
        try:
            response = client.models.generate_content(model=m, contents=prompt)
            text = response.text.strip().replace("```json", "").replace("```", "").strip()
            return json.loads(text)
        except Exception as e:
            print(f"⚠️ {m} busy hai, agla try kar raha hai...")

    raise Exception("❌ Saare models abhi busy hain!")

if __name__ == "__main__":
    data = generate_metadata("GTA 6 crazy police chase in Vice City")
    print(json.dumps(data, indent=2))