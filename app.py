from flask import Flask, request, jsonify, send_from_directory
import os
import uuid
import requests

app = Flask(__name__)

DOWNLOAD_FOLDER = 'downloads'
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

def download_youtube_audio(youtube_url):
    file_id = str(uuid.uuid4())
    filename = f"{file_id}.mp3"
    file_path = os.path.join(DOWNLOAD_FOLDER, filename)
    
    # מנועי הורדה ישירים מובנים
    cobalt_endpoints = [
        "https://cobalt.tools/api/json",
        "https://api.cobalt.tools/api/json"
    ]
    
    payload = {
        "url": youtube_url,
        "isAudioOnly": True,
        "audioFormat": "mp3"
    }
    
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    for endpoint in cobalt_endpoints:
        try:
            print(f"Sending direct link to Cobalt: {endpoint}")
            res = requests.post(endpoint, json=payload, headers=headers, timeout=15)
            if res.status_code == 200:
                res_data = res.json()
                dl_url = res_data.get("url")
                if dl_url:
                    file_res = requests.get(dl_url, stream=True, timeout=45)
                    if file_res.status_code == 200:
                        with open(file_path, 'wb') as f:
                            for chunk in file_res.iter_content(chunk_size=8192):
                                f.write(chunk)
                        return filename
        except Exception as e:
            print(f"Endpoint failed: {e}")
            continue
            
    return None

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'GET':
        return "Direct URL Link Bot is Active!", 200

    data = request.get_json()
    text = data.get("chat", {}).get("messagePayload", {}).get("message", {}).get("text", "").strip()
    
    if not text:
        return jsonify({"text": "שלח לי קישור ישיר של שיר מיוטיוב 🎵"})

    # בדיקה בסיסית אם מדובר בקישור
    if "youtube.com" in text or "youtu.be" in text:
        filename = download_youtube_audio(text)
        if filename:
            stream_url = f"https://music-downloader-bot-7tve.onrender.com/download/{filename}"
            return jsonify({
                "text": f"🎧 השיר שלך הומר בהצלחה למערכת!\n\nלהורדה או האזנה לחץ על הקישור:\n{stream_url}"
            })
        else:
            return jsonify({
                "text": "❌ שרת ההורדות עמוס כרגע. אנא נסה שוב עם קישור זהה או קישור אחר בעוד מספר רגעים."
            })
    else:
        return jsonify({
            "text": "💡 הבוט עבר למצב קישורים חסין-חסימות! אנא שלח קישור יוטיוב מלא (לדוגמה: https://www.youtube.com/watch?v=dQw4w9WgXcQ)"
        })

@app.route('/download/<filename>', methods=['GET'])
def serve_file(filename):
    return send_from_directory(DOWNLOAD_FOLDER, filename, as_attachment=False)

if __name__ == '__main__':
    app.run(port=10000)
