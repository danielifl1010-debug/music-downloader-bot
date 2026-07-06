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
    pattern = r'(?:https?://)?(?:www\.)?(?:youtube\.com/(?:[^/]+/.+/|(?:v|e(?:mbed)?)/|.*[?&]v=)|youtu\.be/)([^"&?/\s]{11})'
    match = re.search(pattern, url)
    return match.group(1) if match else None

def download_via_y2mate_bypass(youtube_url):
    file_id = str(uuid.uuid4())
    filename = f"{file_id}.mp3"
    file_path = os.path.join(DOWNLOAD_FOLDER, filename)
    
    video_id = extract_video_id(youtube_url)
    if not video_id:
        return None

    # שימוש ב-API צד שלישי שממיר עצמאית מחוץ לשרת שלנו ועוקף את חסימת הבוטים של יוטיוב
    convert_url = "https://t-mp3.xyz/api/v1/convert"
    payload = {"url": f"https://www.youtube.com/watch?v={video_id}"}
    
    try:
        print(f"Requesting convert for video ID: {video_id}")
        res = requests.post(convert_url, json=payload, timeout=15)
        if res.status_code == 200:
            data = res.json()
            # שליפת קישור ה-MP3 הישיר שהשרת החיצוני יצר עבורנו
            download_url = data.get("url") or data.get("result")
            
            if download_url:
                print(f"Downloading MP3 from bypass server: {download_url}")
                file_res = requests.get(download_url, stream=True, timeout=45)
                if file_res.status_code == 200:
                    with open(file_path, 'wb') as f:
                        for chunk in file_res.iter_content(chunk_size=8192):
                            f.write(chunk)
                    return filename
    except Exception as e:
        print(f"Bypass system alternative failed: {e}")
        
    # מנוע גיבוי שני (מבוסס שרת הורדות ציבורי מרוחק) במידה והראשון עמוס
    try:
        backup_url = f"https://api.vexdm.com/download?v={video_id}&f=mp3"
        res = requests.get(backup_url, timeout=15).json()
        dl_url = res.get("download_url") or res.get("url")
        if dl_url:
            file_res = requests.get(dl_url, stream=True, timeout=45)
            if file_res.status_code == 200:
                with open(file_path, 'wb') as f:
                    for chunk in file_res.iter_content(chunk_size=8192):
                        f.write(chunk)
                return filename
    except Exception as e:
        print(f"Backup engine failed too: {e}")

    return None

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'GET':
        return "Bypass Downloader is Operational!", 200

    data = request.get_json()
    text = data.get("chat", {}).get("messagePayload", {}).get("message", {}).get("text", "").strip()
    
    if not text:
        return jsonify({"text": "נא לשלוח קישור יוטיוב תקין 🎵"})

    if "youtube.com" in text or "youtu.be" in text:
        clean_url = text.split()[0] if " " in text else text
        filename = download_via_y2mate_bypass(clean_url)
        
        if filename:
            stream_url = f"https://music-downloader-bot-7tve.onrender.com/download/{filename}"
            return jsonify({
                "text": f"🎵 השיר שלך מוכן וממתין להורדה!\n\nלחץ כאן כדי לשמוע או להוריד:\n{stream_url}"
            })
        else:
            return jsonify({
                "text": "❌ שרתי ההמורה החיצוניים עמוסים כרגע. אנא נסה שוב בעוד מספר רגעים."
            })
    else:
        return jsonify({
            "text": "💡 שלח לי קישור ישיר לסרטון מיוטיוב כדי שאמיר אותו עבורך ל-MP3!"
        })

@app.route('/download/<filename>', methods=['GET'])
def serve_file(filename):
    return send_from_directory(DOWNLOAD_FOLDER, filename, as_attachment=False)

if __name__ == '__main__':
    app.run(port=10000)
