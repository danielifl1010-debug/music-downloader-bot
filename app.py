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
    output = os.path.join(DOWNLOAD_FOLDER, f"{file_id}.%(ext)s")

    options = {
        # מבקש אודיו בלבד, עם עדיפות לפורמטים הסטנדרטיים והקלים ביותר להורדה
        "format": "ba/ba*",
        "outtmpl": output,
        "noplaylist": True,
        "quiet": False,
        "default_search": "ytsearch1",
        "socket_timeout": 30,
        # שימוש בארגומנטים שמדמים לקוח iOS/Safari מובנה, שנחשב להרבה יותר יציב מול חסימות
        "extractor_args": {
            "youtube": {
                "player_client": ["ios", "web_safari"],
                "skip": ["dash", "hls"]
            }
        },
        "http_headers": {
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1"
        }
    }

    print(f"--- תחילת תהליך חיפוש עבור: {query} ---")

    with yt_dlp.YoutubeDL(options) as ydl:
        search_query = query if "youtube.com" in query or "youtu.be" in query else f"ytsearch1:{query}"
        
        # חילוץ המידע עם טיפול בשגיאות כדי למנוע קריסת NoneType
        try:
            info = ydl.extract_info(search_query, download=True)
        except Exception as e:
            print(f"שגיאה של yt-dlp בזמן חילוץ המידע: {e}")
            raise Exception("יוטיוב חסם את בקשת ההורדה הנוכחית. נסה שוב בעוד מספר דקות.")

    # בדיקה הגנתית שקיבלנו מידע תקין מיוטיוב
    if info is None:
        raise Exception("לא התקבל מידע מיוטיוב עבור החיפוש הזה.")

    if "entries" in info and len(info["entries"]) > 0:
        title = info["entries"][0].get("title", "שיר")
    else:
        title = info.get("title", "שיר")

    # סריקה דינמית של הקובץ שנוצר פיזית בתיקייה
    files = glob.glob(os.path.join(DOWNLOAD_FOLDER, f"{file_id}.*"))
    if not files:
        raise Exception("הקובץ לא הצליח להישמר בשרת. ייתכן שיוטיוב חסם את הזרם.")

    actual_filename = os.path.basename(files[0])
    print(f"--- ההורדה הושלמה! קובץ שנוצר: {actual_filename} ---")
    return actual_filename, title

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
