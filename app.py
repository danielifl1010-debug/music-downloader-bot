from flask import Flask, request, jsonify, send_file
import os
import uuid
import glob
import yt_dlp

app = Flask(__name__)
DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

def download_song(query):
    file_id = str(uuid.uuid4())
    output = os.path.join(DOWNLOAD_FOLDER, f"{file_id}.mp3")
    
    # אם זה לא לינק, נגדיר לו לחפש ביוטיוב אוטומטית
    search_query = query if query.startswith("http") else f"ytsearch:{query}"
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': output,
        'quiet': True,
        'no_warnings': True,
        # שימוש בלקוח אנדרואיד עוקף הרבה מהחסימות של יוטיוב בשרתי ענן
        'extractor_args': {'youtube': {'player_client': ['android']}},
        'user_agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36'
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([search_query])
    
    return f"{file_id}.mp3", query

@app.route("/", methods=["POST"])
def chat():
    try:
        data = request.json or {}
        text = data.get("message", {}).get("text", "") or data.get("chat", {}).get("messagePayload", {}).get("message", {}).get("text", "")
        if not text: return jsonify({"text": "❌ לא קיבלתי הודעה."})
        
        filename, title = download_song(text)
        return jsonify({"text": f"✅ השיר מוכן: https://music-downloader-bot-7tve.onrender.com/downloads/{filename}"})
    except Exception as e:
        return jsonify({"text": f"❌ שגיאה: {str(e)[:100]}"})

@app.route("/downloads/<filename>")
def download(filename):
    return send_file(os.path.join(DOWNLOAD_FOLDER, filename))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
