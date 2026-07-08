from flask import Flask, request, jsonify, send_file
import os
import uuid
import glob
import time
import re
import requests
import yt_dlp

app = Flask(__name__)

DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

def clean_old_files():
    for f in glob.glob(DOWNLOAD_FOLDER + "/*"):
        try:
            if time.time() - os.path.getmtime(f) > 3600:
                os.remove(f)
        except:
            pass

def search_youtube_link(query):
    """מחפש ביוטיוב ומחלץ את קישור הוידאו הראשון בצורה ידנית וחסינה"""
    try:
        print(f"--- מפעיל חיפוש ישיר ביוטיוב עבור: {query} ---")
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        search_url = f"https://www.youtube.com/results?search_query={requests.utils.quote(query)}"
        response = requests.get(search_url, headers=headers, timeout=15)
        
        video_ids = re.findall(r"\"videoId\":\"([^\"]+)\"", response.text)
        
        if video_ids:
            first_id = video_ids[0]
            video_url = f"https://www.youtube.com/watch?v={first_id}"
            print(f"--- נמצא מזהה סרטון: {first_id} -> {video_url} ---")
            return video_url, query
            
    except Exception as e:
        print(f"שגיאה במנגנון החיפוש הישיר: {e}")
    
    return None, None

def download_song(query):
    clean_old_files()
    file_id = str(uuid.uuid4())
    output = os.path.join(DOWNLOAD_FOLDER, f"{file_id}.%(ext)s")

    if "youtube.com" not in query and "youtu.be" not in query:
        video_url, video_title = search_youtube_link(query)
        if not video_url:
            raise Exception("לא הצלחתי למצוא תוצאות עבור השיר הזה ביוטיוב.")
        target_url = video_url
    else:
        target_url = query

    options = {
        "format": "ba/ba*",
        "outtmpl": output,
        "noplaylist": True,
        "quiet": False,
        "socket_timeout": 30,
        # שימוש בקליינט אינטרנט רגיל לחלוטין שעובד יציב
        "extractor_args": {
            "youtube": {
                "player_client": ["web"],
                "skip": ["dash", "hls"]
            }
        },
        "http_headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
    }

    print(f"--- yt-dlp מתחיל הורדה ישירה מהקישור: {target_url} ---")

    try:
        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(target_url, download=True)
            
        if info is None:
            raise Exception("יוטיוב החזיר תשובה ריקה בניסיון ההורדה.")

        title = info.get("title", "שיר")

        files = glob.glob(os.path.join(DOWNLOAD_FOLDER, f"{file_id}.*"))
        if not files:
            raise Exception("הקובץ לא נשמר בשרת הענן.")

        actual_filename = os.path.basename(files[0])
        print(f"--- ההורדה הסתיימה בהצלחה! קובץ נוצר: {actual_filename} ---")
        return actual_filename, title

    except Exception as e:
        print(f"שגיאה בזמן ההורדה של yt-dlp: {e}")
        raise Exception(f"יוטיוב חסם את הזרם מהכתובת הזו. שגיאה: {str(e)[:50]}")

@app.route("/", methods=["POST"])
def chat():
    try:
        data = request.json or {}
        text = ""
        if "chat" in data:
            text = data["chat"].get("messagePayload", {}).get("message", {}).get("text", "")
        elif "message" in data:
            text = data["message"].get("text", "")

        if not text:
            return jsonify({"text": "❌ לא קיבלתי שם שיר או הודעה תקינה בפורמט."})

        filename, title = download_song(text)
        url = f"https://music-downloader-bot-7tve.onrender.com/downloads/{filename}"

        return jsonify({
            "text": f"🎵 **{title}**\n\n⬇️ השיר מוכן להורדה! לחץ על הקישור:\n{url}"
        })

    except Exception as e:
        print("שגיאה בזמן הריצה:", e)
        return jsonify({
            "text": f"❌ שגיאה בהורדת השיר:\n{str(e)[:250]}"
        })

@app.route("/downloads/<filename>")
def downloads(filename):
    if filename.endswith(".m4a"):
        mimetype = "audio/mp4"
    elif filename.endswith(".webm"):
        mimetype = "audio/webm"
    else:
        mimetype = "audio/mpeg"
        
    return send_file(
        os.path.join(DOWNLOAD_FOLDER, filename),
        as_attachment=True,
        mimetype=mimetype
    )

@app.route("/health")
def health():
    return "OK"

@app.route("/", methods=["GET"])
def home():
    return "Direct Downloader Bot is fully stable!"

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 10000))
    )
