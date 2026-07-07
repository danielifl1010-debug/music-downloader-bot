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

# שליחת המפתח בצורה מאובטחת ממשתני הסביבה של Render
RAPIDAPI_KEY = os.environ.get("RAPIDAPI_KEY")

def clean_old_files():
    for old_file in glob.glob(DOWNLOAD_FOLDER + "/*"):
        try:
            if time.time() - os.path.getmtime(old_file) > 3600:
                os.remove(old_file)
        except:
            pass

def get_youtube_video_id(query):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    # אם המשתמש שלח קישור ישיר
    if "youtube.com" in query or "youtu.be" in query:
        found = re.findall(r"(?:v=|\/)([a-zA-Z0-9_-]{11})", query)
        if found:
            return found[0]

    # חיפוש טקסטואלי במובייל יוטיוב (חסין ועוקף חסימות)
    try:
        url = "https://m.youtube.com/results?search_query=" + requests.utils.quote(query)
        res = requests.get(url, headers=headers, timeout=10)
        ids = re.findall(r'"videoId":"([a-zA-Z0-9_-]{11})"', res.text)
        if ids:
            return ids[0]
    except Exception as e:
        print("חיפוש מובייל נכשל:", e)

    return None

def download_song(query):
    clean_old_files()

    if not RAPIDAPI_KEY:
        raise Exception("חסר RAPIDAPI_KEY בהגדרות Render")

    video_id = get_youtube_video_id(query)

    if not video_id:
        raise Exception("לא הצלחתי למצוא את השיר ביוטיוב. נסה שם אחר.")

    print("Video ID נמצא:", video_id)

    # עדכון ל-API החדש והיציב ביותר (youtube-mp36)
    api_url = "https://youtube-mp36.p.rapidapi.com/dl"
    
    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": "youtube-mp36.p.rapidapi.com"
    }

    try:
        response = requests.get(
            api_url,
            headers=headers,
            params={"id": video_id},
            timeout=30
        )

        if response.status_code != 200:
            raise Exception(f"RapidAPI error {response.status_code}")

        try:
            data = response.json()
        except:
            raise Exception("RapidAPI לא החזיר JSON תקין")

        # ה-API הזה מחזיר את הקישור תחת המפתח 'link'
        download_url = data.get("link")

        if not download_url:
            # אם הסטטוס אומר שהוא עדיין מעבד, ניתן הודעה ידידותית
            if data.get("msg") or data.get("status") == "processing":
                raise Exception("השרת מעבד את השיר כרגע. נסה שוב בעוד כמה שניות.")
            raise Exception("לא נמצא קישור הורדה בתשובת השרת")

        print("מוריד מקישור ישיר:", download_url)

        file_id = str(uuid.uuid4())
        filename = file_id + ".mp3"
        path = os.path.join(DOWNLOAD_FOLDER, filename)

        file_response = requests.get(download_url, stream=True, timeout=60)

        if file_response.status_code != 200:
            raise Exception("שגיאה בהורדת קובץ האודיו משרת האחסון")

        # שמירת הקובץ בשרת בלוקים-בלוקים (Stream) כדי לא להעמיס על הזיכרון
        with open(path, "wb") as f:
            for chunk in file_response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        return filename

    except Exception as e:
        print("DOWNLOAD ERROR:", e)
        raise e

@app.route("/", methods=["POST"])
def chat():
    try:
        data = request.json or {}
        text = ""

        if "chat" in data:
            text = data.get("chat", {}).get("messagePayload", {}).get("message", {}).get("text", "")
        elif "message" in data:
            text = data["message"].get("text", "")

        if not text:
            return jsonify({"text": "❌ לא קיבלתי שם שיר"})

        print("בקשה שהתקבלה:", text)
        filename = download_song(text)

        url = "https://music-downloader-bot-7tve.onrender.com/downloads/" + filename

        return jsonify({
            "text": "🎵 **השיר מוכן!**\n\n⬇️ לחץ על הקישור הבא להורדה:\n" + url
        })

    except Exception as e:
        print("ERROR:", e)
        return jsonify({
            "text": "❌ שגיאה:\n" + str(e)[:300]
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
