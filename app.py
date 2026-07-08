from flask import Flask, request, jsonify, send_file
import os
import uuid
import glob
import time
import yt_dlp
import requests

app = Flask(__name__)
DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

def get_proxy():
    # שרת שמוצא פרוקסים עובדים בזמן אמת כדי לעקוף את החסימה של Render
    try:
        proxies = requests.get("https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all", timeout=5).text.split('\r\n')
        return f"http://{proxies[0]}" # לוקח פרוקסי טרי
    except:
        return None

def download_song(query):
    file_id = str(uuid.uuid4())
    output = os.path.join(DOWNLOAD_FOLDER, f"{file_id}.mp3")
    
    # הגדרות קיצוניות לעקיפת חסימות
    proxy_url = get_proxy()
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': output,
        'proxy': proxy_url,
        'quiet': True,
        'no_warnings': True,
        'extractor_args': {'youtube': {'player_client': ['android', 'ios']}},
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
    }
    
    print(f"--- מוריד דרך פרוקסי: {proxy_url} ---")
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([query])
    
    return f"{file_id}.mp3", "השיר"

@app.route("/", methods=["POST"])
def chat():
    # ... (אותו לוגיקה של הודעות כמו קודם)
    data = request.json
    text = data.get("message", {}).get("text", "") if "message" in data else data.get("chat", {}).get("messagePayload", {}).get("message", {}).get("text", "")
    
    filename, title = download_song(text)
    return jsonify({"text": f"✅ השיר מוכן: https://music-downloader-bot-7tve.onrender.com/downloads/{filename}"})

@app.route("/downloads/<filename>")
def download(filename):
    return send_file(os.path.join(DOWNLOAD_FOLDER, filename))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
