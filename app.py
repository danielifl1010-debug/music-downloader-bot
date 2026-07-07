from flask import Flask, request, jsonify, send_file
import os
import uuid
import glob
import time
import requests

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

def download_song(query):
    clean_old_files()
    file_id = str(uuid.uuid4())
    filename = f"{file_id}.mp3"
    file_path = os.path.join(DOWNLOAD_FOLDER, filename)
    
    # שלב 1: חיפוש ביוטיוב דרך מנוע פתוח לקבלת מזהה הסרטון (Video ID)
    try:
        print(f"מחפש ביוטיוב: {query}")
        search_url = f"https://io.sccon.top/search?q={requests.utils.quote(query)}"
        search_res = requests.get(search_url, timeout=10).json()
        
        if search_res and isinstance(search_res, list) and len(search_res) > 0:
            video_id = search_res[0].get('id')
            title = search_res[0].get('title', 'שיר')
            print(f"נמצא סרטון: {title} (ID: {video_id})")
        else:
            raise Exception("לא נמצאו תוצאות חיפוש")
            
    except Exception as e:
        print(f"חיפוש נכשל: {e}")
        raise Exception("לא הצלחתי למצוא את השיר ביוטיוב.")

    # שלב 2: פנייה לשרתי המרה חיצוניים חסיני-חסימות לקבלת קובץ ה-MP3
    bypass_apis = [
        f"https://api.vexdm.com/download?v={video_id}&f=mp3",
        f"https://api.download.tube/api/v1/download?url=https://www.youtube.com/watch?v={video_id}&format=mp3"
    ]
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    for url in bypass_apis:
        try:
            print(f"מנסה להוריד משרת המרה חיצוני: {url}")
            res = requests.get(url, headers=headers, timeout=15)
            if res.status_code == 200:
                res_data = res.json()
                dl_url = res_data.get("download_url") or res_data.get("url") or res_data.get("link")
                
                if dl_url:
                    print(f"מוריד קובץ זרם מ-: {dl_url}")
                    file_res = requests.get(dl_url, stream=True, headers=headers, timeout=45)
                    if file_res.status_code == 200:
                        with open(file_path, 'wb') as f:
                            for chunk in file_res.iter_content(chunk_size=8192):
                                f.write(chunk)
                        return filename, title
        except Exception as e:
            print(f"מנוע המרה ספציפי נכשל: {e}")
            continue

    raise Exception("שרתי ההמורה החיצוניים עמוסים כרגע. נסה שוב בעוד רגע.")

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

        print("בקשת הורדה מהצ'אט עבור:", text)
        filename, title = download_song(text)

        # קישור HTTPS קבוע ומאובטח המותאם לשרת Render שלך
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
