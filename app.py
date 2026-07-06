from flask import Flask, request, jsonify, send_from_directory
import os
import uuid
import requests

app = Flask(__name__)

DOWNLOAD_FOLDER = 'downloads'
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

def try_cobalt_download(api_url, youtube_url, file_path):
    """פונקציית עזר לניסיון הורדה משרת קובלט ספציפי"""
    try:
        payload = {
            "url": youtube_url,
            "isAudioOnly": True,
            "audioFormat": "mp3",
            "vCodec": "h264",
            "audioBitrate": "128"
        }
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }
        res = requests.post(api_url, json=payload, headers=headers, timeout=10)
        if res.status_code == 200:
            res_data = res.json()
            dl_url = res_data.get("url")
            if dl_url:
                file_res = requests.get(dl_url, stream=True, timeout=30)
                if file_res.status_code == 200:
                    with open(file_path, 'wb') as f:
                        for chunk in file_res.iter_content(chunk_size=8192):
                            f.write(chunk)
                    return True
    except Exception as e:
        print(f"Failed endpoint {api_url}: {e}")
    return False

def download_youtube_audio(youtube_url):
    file_id = str(uuid.uuid4())
    filename = f"{file_id}.mp3"
    file_path = os.path.join(DOWNLOAD_FOLDER, filename)
    
    # רשימת שרתי קובלט ציבוריים ומהירים ברחבי העולם לעקיפת חסימות רשת
    endpoints = [
        "https://cobalt.tools/api/json",
        "https://api.cobalt.tools/api/json",
        "https://co.wuk.sh/api/json",
        "https://cobalt.api.g9ee.xyz/api/json"
    ]
    
    # ניסיון חזרה (Fallback) על כל השרתים אחד אחרי השני
    for api_url in endpoints:
        print(f"Trying download from: {api_url}")
        success = try_cobalt_download(api_url, youtube_url, file_path)
        if success:
            return filename
            
    return None

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'GET':
        return "Multi-Endpoint Downloader Bot is Active!", 200

    data = request.get_json()
    text = data.get("chat", {}).get("messagePayload", {}).get("message", {}).get("text", "").strip()
    
    if not text:
        return jsonify({"text": "אנא שלח לי קישור ישיר לשיר מיוטיוב 🎵"})

    # בדיקה האם המשתמש שלח קישור תקין של יוטיוב
    if "youtube.com" in text or "youtu.be" in text:
        # ניקוי תווים מיותרים מהקישור במידה והגיעו עם רווחים
        clean_url = text.split()[0] if " " in text else text
        
        filename = download_youtube_audio(clean_url)
        if filename:
            stream_url = f"https://music-downloader-bot-7tve.onrender.com/download/{filename}"
            return jsonify({
                "text": f"🎧 השיר שלך עובד והורד בהצלחה!\n\nלחץ על הקישור הבא כדי להוריד או להאזין ל-MP3:\n{stream_url}"
            })
        else:
            return jsonify({
                "text": "❌ כל שרתי ההורדה חסמו את הבקשה כרגע או שהסרטון ארוך מדי. אנא נסה שוב עם קישור אחר בעוד רגע."
            })
    else:
        return jsonify({
            "text": "💡 נא לשלוח קישור יוטיוב ישיר בלבד!\nלדוגמה: https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        })

@app.route('/download/<filename>', methods=['GET'])
def serve_file(filename):
    return send_from_directory(DOWNLOAD_FOLDER, filename, as_attachment=False)

if __name__ == '__main__':
    app.run(port=10000)
