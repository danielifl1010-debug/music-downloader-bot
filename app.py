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

def download_via_fallback_api(video_url, output_path):
    """מנגנון גיבוי חסין חסימות - מוריד את האודיו דרך שרת צד שלישי שאינו חסום"""
    try:
        print("--- מפעיל מנגנון עקירת חסימה (Fallback API) ---")
        video_id = video_url.split("v=")[-1].split("&")[0] if "v=" in video_url else video_url.split("/")[-1]
        
        # שימוש ב-API מהיר וציבורי להמרת יוטיוב ל-MP3
        api_url = f"https://api.vexdile.com/v1/youtube/download?id={video_id}&type=mp3"
        res = requests.get(api_url, timeout=30).json()
        
        download_link = res.get("download_url") or res.get("url")
        if not download_link:
            # ניסיון שני עם API חלופי נפוץ
            api_url = f"https://api.fabdl.com/youtube/get-video-info?url={requests.utils.quote(video_url)}"
            info = requests.get(api_url, timeout=20).json()
            # שליפת קישור ישיר
            mp3_api = f"https://api.fabdl.com/youtube/convert-task/{info['result']['id']}/{info['result']['audio'][0]['id']}"
            download_link = requests.get(mp3_api, timeout=20).json()['result']['download_url']
            
        if download_link:
            print(f"--- קישור הורדה עוקף חסימה חולץ בהצלחה. מתחיל הורדת קובץ לשרת... ---")
            file_res = requests.get(download_link, timeout=60, stream=True)
            with open(output_path, "wb") as f:
                for chunk in file_res.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            return True
    except Exception as e:
        print(f"מנגנון הגיבוי נכשיל גם הוא: {e}")
    return False

def download_song(query):
    clean_old_files()
    file_id = str(uuid.uuid4())
    # שומרים כ-mp3 כברירת מחדל אחידה
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
        "socket_timeout": 15,
        "extractor_args": {
            "youtube": {
                "player_client": ["tv", "web"],
                "skip": ["dash", "hls"]
            }
        }
    }

    print(f"--- ניסיון הורדה רגיל עבור: {target_url} ---")
    try:
        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(target_url, download=True)
            video_title = info.get("title", video_title)
            
        files = glob.glob(os.path.join(DOWNLOAD_FOLDER, f"{file_id}.*"))
        if files:
            return os.path.basename(files[0]), video_title
    except Exception as e:
        print(f"יוטיוב חסם את הבקשה הרגילה ({e}). עובר מיד למנגנון חסין חסימות...")
        
    # אם הגענו לכאן, השרת של Render חסום על ידי יוטיוב - מפעילים את הפתרון החלופי
    success = download_via_fallback_api(target_url, output)
    if success and os.path.exists(output):
        return output_filename, video_title
        
    raise Exception("יוטיוב חוסם את השרת באופן קבוע וכל מנגנוני העקיפה נכשלו כרגע.")

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
    return "Direct Downloader Bot with Advanced Anti-Block Bypass is Live!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
