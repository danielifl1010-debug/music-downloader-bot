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
    for old_file in glob.glob(DOWNLOAD_FOLDER + "/*"):
        try:
            if time.time() - os.path.getmtime(old_file) > 3600:
                os.remove(old_file)
        except:
            pass

def download_song_direct(query):
    clean_old_files()
    
    file_id = str(uuid.uuid4())
    filename = f"{file_id}.mp3"
    file_path = os.path.join(DOWNLOAD_FOLDER, filename)
    
    print(f"מתחיל חיפוש והורדה ישירה עבור: {query}")
    
    # הגדרות עבור yt-dlp להורדת אודיו בלבד בפורמט MP3
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(DOWNLOAD_FOLDER, file_id),  # שם זמני לקובץ
        'noplaylist': True,
        'default_search': 'ytsearch1',  # מחפש ביוטיוב ולוקח את התוצאה הראשונה
        'quiet': False,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        # הוספת תגיות דפדפן כדי למנוע חסימות בוטים משרתי ענן
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # מריץ את החיפוש וההורדה
            info = ydl.extract_info(query, download=True)
            
            # שליפת שם השיר האמיתי מתוך יוטיוב בשביל ההודעה
            video_title = query
            if 'entries' in info and len(info['entries']) > 0:
                video_title = info['entries'][0].get('title', query)
            elif 'title' in info:
                video_title = info.get('title', query)
                
            print(f"הורדה והמרה מקומית הושלמו עבור: {video_title}")
            return filename, video_title
            
    except Exception as e:
        print(f"שגיאה בהורדה ישירה עם yt-dlp: {e}")
        raise Exception("לא הצלחתי להוריד את השיר מיוטיוב. נסה שם אחר.")

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

        print("בקשה שהתקבלה בצ'אט:", text)
        filename, title = download_song_direct(text)

        url = f"https://music-downloader-bot-7tve.onrender.com/downloads/{filename}"

        return jsonify({
            "text": f"🎵 **הורדת השיר הושלמה בהצלחה!**\n\n**שם השיר:** {title}\n\n⬇️ לחץ על הקישור הבא להורדה:\n{url}"
        })

    except Exception as e:
        print("ERROR:", e)
        return jsonify({
            "text": f"❌ שגיאה בהורדה:\n{str(e)[:300]}"
        })

@app.route("/downloads/<filename>")
def downloads(filename):
    # החזרת הקובץ עם סיומת mp3 ושם קובץ אטצ'מנט
    return send_file(
        os.path.join(DOWNLOAD_FOLDER, filename),
        as_attachment=True,
        mimetype="audio/mpeg"
    )

@app.route("/health")
def health():
    return "OK"

@app.route("/", methods=["GET"])
def home():
    return "Direct Downloader Bot is running!"

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 10000))
    )
