from flask import Flask, request, jsonify, send_from_directory
import os
import uuid
import requests
import re

app = Flask(__name__)

DOWNLOAD_FOLDER = 'downloads'
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

def extract_video_id(url):
    """חילוץ מזהה הוידאו של יוטיוב מהקישור"""
    pattern = r'(?:https?://)?(?:www\.)?(?:youtube\.com/(?:[^/]+/.+/|(?:v|e(?:mbed)?)/|.*[?&]v=)|youtu\.be/)([^"&?/\s]{11})'
    match = re.search(pattern, url)
    return match.group(1) if match else None

def download_youtube_audio(youtube_url):
    file_id = str(uuid.uuid4())
    filename = f"{file_id}.mp3"
    file_path = os.path.join(DOWNLOAD_FOLDER, filename)
    
    video_id = extract_video_id(youtube_url)
    if not video_id:
        print("Could not extract video ID")
        return None

    # שימוש ב-API הורדות אלטרנטיבי חזק וחסין לחלוטין מפני חסימות של Render
    api_urls = [
        f"https://api.vexdm.com/download?v={video_id}&f=mp3",
        f"https://api.download.tube/api/v1/download?url={requests.utils.quote(youtube_url)}&format=mp3"
    ]
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    for url in api_urls:
        try:
            print(f"Trying download from alternative API: {url}")
            # פנייה ראשונית לקבלת קישור ההורדה הישיר של ה-MP3
            res = requests.get(url, headers=headers, timeout=15)
            if res.status_code == 200:
                res_data = res.json()
                # שליפת הקישור לקובץ לפי מבני תגובה נפוצים
                dl_url = res_data.get("download_url") or res_data.get("url") or res_data.get("link")
                
                if dl_url:
                    print(f"Downloading stream from: {dl_url}")
                    file_res = requests.get(dl_url, stream=True, headers=headers, timeout=45)
                    if file_res.status_code == 200:
                        with open(file_path, 'wb') as f:
                            for chunk in file_res.iter_content(chunk_size=8192):
                                f.write(chunk)
                        return filename
        except Exception as e:
            print(f"Alternative endpoint failed: {e}")
            continue
            
    return None

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'GET':
        return "Bypass Downloader Bot Server is Active!", 200

    data = request.get_json()
    text = data.get("chat", {}).get("messagePayload", {}).get("message", {}).get("text", "").strip()
    
    if not text:
        return jsonify({"text": "אנא שלח לי קישור ישיר לשיר מיוטיוב 🎵"})

    if "youtube.com" in text or "youtu.be" in text:
        clean_url = text.split()[0] if " " in text else text
        
        filename = download_youtube_audio(clean_url)
        if filename:
            stream_url = f"https://music-downloader-bot-7tve.onrender.com/download/{filename}"
            return jsonify({
                "text": f"🎧 השיר הומר והורד בהצלחה!\n\nלחץ על הקישור הבא כדי להאזין או להוריד:\n{stream_url}"
            })
        else:
            return jsonify({
                "text": "❌ שרת ההורדות חסם את הבקשה. אנא נסה שוב עם קישור אחר בעוד מספר רגעים."
            })
    else:
        return jsonify({
            "text": "💡 הבוט מקבל קישורי יוטיוב ישירים בלבד!\nלדוגמה: https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        })

@app.route('/download/<filename>', methods=['GET'])
def serve_file(filename):
    return send_from_directory(DOWNLOAD_FOLDER, filename, as_attachment=False)

if __name__ == '__main__':
    app.run(port=10000)
