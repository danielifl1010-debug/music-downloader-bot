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

def download_via_cobalt_fallback(video_url, output_path):
    """מנגנון על-חסין מבוסס Cobalt API ושרתי קהילה מבוזרים לעקיפת חסימות יוטיוב"""
    # רשימת שרתי Cobalt ציבוריים מעודכנים ויציבים
    cobalt_instances = [
        "https://api.cobalt.tools",
        "https://cobalt.moe/api",
        "https://api.b64.to",
        "https://pygmalion.cobalt.tools"
    ]
    
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    payload = {
        "url": video_url,
        "videoQuality": "720",
        "audioFormat": "mp3",
        "isAudioOnly": True,
        "filenamePattern": "classic"
    }
    
    for instance in cobalt_instances:
        try:
            print(f"--- מנסה לחלץ אודיו דרך שרת Cobalt: {instance} ---")
            # קריאה לקובלט לחילוץ הסטרים
            res = requests.post(f"{instance}/stream", json=payload, headers=headers, timeout=15)
            if res.status_code == 200:
                data = res.json()
                download_link = data.get("url")
                
                if download_link:
                    print(f"--- הצלחה! נמצא קישור ישיר לעקיפת חסימה. מוריד קובץ לשרת... ---")
                    # הורדת הסטרים הציבורי שקובלט יצר עבורנו
                    file_res = requests.get(download_link, timeout=45, stream=True)
                    with open(output_path, "wb") as f:
                        for chunk in file_res.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                    print("--- הקובץ ירד בהצלחה משרת הגיבוי! ---")
                    return True
            print(f"שרת {instance} החזיר סטטוס {res.status_code}, מנסה את השרת הבא ברשימה...")
        except Exception as e:
            print(f"שגיאה בתקשורת מול {instance}: {e}")
            continue
            
    return False

def download_song(query):
    clean_old_files()
    file_id = str(uuid.uuid4())
    output_filename = f"{file_id}.mp3"
    output = os.path.join(DOWNLOAD_FOLDER, output_filename)

    if "youtube.com" not in query and "youtu.be" not in query:
        video_url, video_title = search_youtube_link(query)
        if not video_url:
            raise Exception("לא הצלחתי למצוא תוצאות עבור השיר הזה ביוטיוב.")
        target_url = video_url
    else:
        target_url = query
        video_title = "שיר מיוטיוב"

    options = {
        "format": "ba/ba*",
        "outtmpl": os.path.join(DOWNLOAD_FOLDER, f"{file_id}.%(ext)s"),
        "noplaylist": True,
        "quiet": True,
        "socket_timeout": 12,
        "extractor_args": {
            "youtube": {
                "player_client": ["tv"],
                "skip": ["dash", "hls"]
            }
        }
    }

    print(f"--- ניסיון הורדה ישיר עבור: {target_url} ---")
    try:
        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(target_url, download=True)
            video_title = info.get("title", video_title)
            
        files = glob.glob(os.path.join(DOWNLOAD_FOLDER, f"{file_id}.*"))
        if files:
            return os.path.basename(files[0]), video_title
    except Exception as e:
        print(f"יוטיוב חסם את השרת באופן ישיר. מפעיל מיד רשת שרתי גיבוי מבוזרת...")
        
    # הפעלה של רשת הגיבוי המבוזרת של קובלט
    success = download_via_cobalt_fallback(target_url, output)
    if success and os.path.exists(output):
        return output_filename, video_title
        
    raise Exception("כל שרתי הגיבוי ועקיפת החסימות עמוסים או חסומים כרגע. אנא נסה שוב בעוד מספר רגעים.")

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
    mimetype = "audio/mpeg"
    if filename.endswith(".m4a"):
        mimetype = "audio/mp4"
    elif filename.endswith(".webm"):
        mimetype = "audio/webm"
    return send_file(os.path.join(DOWNLOAD_FOLDER, filename), as_attachment=True, mimetype=mimetype)

@app.route("/health")
def health():
    return "OK"

@app.route("/", methods=["GET"])
def home():
    return "Direct Downloader Bot with Distributed Cobalt Bypass Network is Live!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
