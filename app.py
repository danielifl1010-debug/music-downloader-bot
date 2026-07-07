from flask import Flask, request, jsonify, send_file
import os
import uuid
import glob
import time
import requests
import re

app = Flask(__name__)

DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

def clean_old_files():
    for old_file in glob.glob(DOWNLOAD_FOLDER + "/*"):
        try:
            if time.time() - os.path.getmtime(old_file) > 3600:
                os.remove(old_file)
        except:
            pass

def get_youtube_video_id(query):
    """מנוע חילוץ מזהה וידאו אגרסיבי ויציב - מנסה מספר שיטות שונות"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    # שיטה 1: סקראפינג ישיר מיוטיוב מובייל (פחות נוטה להיחסם)
    try:
        url = f"https://m.youtube.com/results?search_query={requests.utils.quote(query)}"
        res = requests.get(url, headers=headers, timeout=10)
        video_ids = re.findall(r"\"videoId\":\"([a-zA-Z0-9_-]{11})\"", res.text)
        if video_ids:
            return video_ids[0]
    except Exception as e:
        print(f"Mobile scrape failed: {e}")

    # שיטה 2: סקראפינג מיוטיוב דסקטופ (גיבוי)
    try:
        url = f"https://www.youtube.com/results?search_query={requests.utils.quote(query)}"
        res = requests.get(url, headers=headers, timeout=10)
        video_ids = re.findall(r"watch\?v=([a-zA-Z0-9_-]{11})", res.text)
        if video_ids:
            return video_ids[0]
    except Exception as e:
        print(f"Desktop scrape failed: {e}")

    return None

def download_song(query):
    clean_old_files()
    file_id = str(uuid.uuid4())
    filename = f"{file_id}.mp3"
    file_path = os.path.join(DOWNLOAD_FOLDER, filename)
    
    # שלב 1: מציאת ה-Video ID של השיר
    print(f"מאתר מזהה וידאו עבור: {query}")
    video_id = get_youtube_video_id(query)
    
    if not video_id:
        raise Exception("לא הצלחתי למצוא את השיר ביוטיוב. נסה שם מדויק יותר.")
        
    youtube_url = f"https://www.youtube.com/watch?v={video_id}"
    print(f"נמצא סרטון: {youtube_url} | מנסה להוריד...")

    # שלב 2: שימוש בשרתי פרויקט Cobalt הרשמיים המבוזרים (עוקפים חסימות IP)
    # ננסה מספר קצוות (Endpoints) שונים של Cobalt כדי להבטיח זמינות
    cobalt_instances = [
        "https://api.cobalt.tools",
        "https://cobalt.api.v0.ru",
        "https://api.cobalt.tools/api/json"
    ]
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    payload = {
        "url": youtube_url,
        "videoQuality": "720",
        "audioFormat": "mp3",
        "isAudioOnly": True
    }

    for instance in cobalt_instances:
        try:
            print(f"מנסה שרת המרה: {instance}")
            
            # תיקון קטן לכתובת במידת הצורך
            endpoint = instance if instance.endswith("/json") else f"{instance}/"
            if not endpoint.endswith("/json") and not endpoint.endswith("/"): endpoint += "/api/json"
            
            res = requests.post(instance if "api/json" in instance else f"{instance}", json=payload, headers=headers, timeout=15)
            
            if res.status_code == 200:
                res_data = res.json()
                dl_url = res_data.get("url")
                
                if dl_url:
                    print(f"ההמרה הצליחה! מוריד קובץ זרם מ-: {dl_url}")
                    file_res = requests.get(dl_url, stream=True, timeout=60)
                    if file_res.status_code == 200:
                        with open(file_path, 'wb') as f:
                            for chunk in file_res.iter_content(chunk_size=8192):
                                f.write(chunk)
                        return filename, query
        except Exception as e:
            print(f"שרת המרה {instance} נכשל: {e}")
            continue

    # מנוע גיבוי אחרון: שרת API ייעודי להורדות ישירות ללא JSON מורכב
    try:
        print("מנסה מנוע גיבוי ישיר (Y2Mate API Proxy)...")
        backup_url = f"https://server2.mp3q.cc/api/v1/download?url={requests.utils.quote(youtube_url)}"
        file_res = requests.get(backup_url, stream=True, timeout=45)
        if file_res.status_code == 200 and len(file_res.content) > 50000: # לוודא שזה לא דף שגיאה קטן
            with open(file_path, 'wb') as f:
                f.write(file_res.content)
            return filename, query
    except Exception as e:
        print(f"מנוע גיבוי ישיר נכשל: {e}")

    raise Exception("כל שרתי ההורדה וההמרה חסמו את הבקשה מהשרת הנוכחי. נסה שוב בעוד דקה.")

@app.route("/", methods=["POST"])
def chat():
    try:
        data = request.json or {}
        text = ""

        if "chat" in data:
            text = data["chat"]["messagePayload"]["message"]["text"]
        elif "message" in data:
            text = data["message"].get("text", "")

        if not text:
            return jsonify({"text": "❌ לא קיבלתי שם שיר"})

        print("בקשת הורדה עבור:", text)
        filename, title = download_song(text)

        url = f"https://music-downloader-bot-7tve.onrender.com/downloads/{filename}"

        return jsonify({
            "text": f"🎵 **{title}**\n\n⬇️ השיר מוכן! לחץ על הקישור להורדה:\n{url}"
        })

    except Exception as e:
        print("ERROR:", e)
        return jsonify({
            "text": f"❌ שגיאה:\n{str(e)[:500]}"
        })

@app.route("/downloads/<filename>")
def downloads(filename):
    return send_file(
        os.path.join(DOWNLOAD_FOLDER, filename),
        as_attachment=True
    )

@app.route("/health")
def health():
    return "OK"

@app.route("/", methods=["GET"])
def home():
    return "Bot is running"

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 10000))
    )
