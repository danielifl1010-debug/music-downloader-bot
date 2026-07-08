from flask import Flask, request, jsonify, send_file
import os
import uuid
import glob
import time
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

def download_song(query):
    clean_old_files()
    file_id = str(uuid.uuid4())
    
    # שמירה בפורמט m4a קליל כדי לא להצטרך ffmpeg ב-Render
    output = os.path.join(DOWNLOAD_FOLDER, f"{file_id}.%(ext)s")

    options = {
        "format": "bestaudio[ext=m4a]/bestaudio/best",
        "outtmpl": output,
        "noplaylist": True,
        "quiet": False,
        "default_search": "ytsearch1",
        "socket_timeout": 30,
        "http_headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
    }

    print(f"--- תחילת תהליך חיפוש עבור: {query} ---")

    with yt_dlp.YoutubeDL(options) as ydl:
        # אם המשתמש שלח קישור ישיר נשתמש בו, אחרת נחפש
        search_query = query if "youtube.com" in query or "youtu.be" in query else f"ytsearch1:{query}"
        info = ydl.extract_info(search_query, download=True)

    if "entries" in info and len(info["entries"]) > 0:
        title = info["entries"][0]["title"]
    else:
        title = info.get("title", "שיר")

    # בדיקה איזה קובץ פיזית נוצר בתיקייה
    files = glob.glob(os.path.join(DOWNLOAD_FOLDER, f"{file_id}.*"))

    if not files:
        raise Exception("קובץ השמע לא נשמר בהצלחה בשרת הענן.")

    actual_filename = os.path.basename(files[0])
    print(f"--- ההורדה הסתיימה בהצלחה! קובץ נוצר: {actual_filename} ---")
    return actual_filename, title

@app.route("/", methods=["POST"])
def chat():
    try:
        data = request.json or {}
        print("מידע גולמי שהתקבל בשרת:", data)
        
        text = ""
        if "chat" in data:
            text = data["chat"].get("messagePayload", {}).get("message", {}).get("text", "")
        elif "message" in data:
            text = data["message"].get("text", "")

        if not text:
            return jsonify({"text": "❌ לא קיבלתי שם שיר או הודעה תקינה בפורמט."})

        print(f"מפעיל הורדה עבור הטקסט: {text}")
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
    mimetype = "audio/mp4" if filename.endswith(".m4a") else "audio/mpeg"
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
    return "Direct Downloader Bot is live and kicking!"

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 10000))
    )
