from flask import Flask, request, jsonify, send_file
import os
import uuid
import glob
import time
import re
import requests

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

def download_via_global_mesh(video_url, output_path):
    """ארכיטקטורת 100 צעדים קדימה: רשת שרתים עולמית ברוטציה אוטומטית"""
    video_id = video_url.split("v=")[-1].split("&")[0] if "v=" in video_url else video_url.split("/")[-1]
    
    # רשת שרתי קצה מבוזרים (Piped & Invidious Mesh)
    global_endpoints = [
        "https://pipedapi.kavin.rocks/streams/",
        "https://api.piped.yt/streams/",
        "https://pipedapi.tokyo.moe/streams/",
        "https://piped-api.garudalinux.org/streams/",
        "https://invidious.nerdvpn.de/api/v1/videos/",
        "https://yewtu.be/api/v1/videos/",
        "https://iv.melmac.space/api/v1/videos/"
    ]
    
    for endpoint in global_endpoints:
        try:
            print(f"--- רשת הרוטציה מנסה לעקוף חסימה דרך: {endpoint} ---")
            url = f"{endpoint}{video_id}"
            res = requests.get(url, timeout=10)
            
            if res.status_code != 200:
                continue
                
            data = res.json()
            title = data.get("title", "שיר מיוטיוב")
            direct_audio_url = None
            
            # אם זה שרת מסוג Piped API
            if "audioStreams" in data:
                audio_streams = data.get("audioStreams", [])
                if audio_streams:
                    # לוקחים את האיכות הגבוהה ביותר
                    audio_streams.sort(key=lambda x: x.get("bitrate", 0), reverse=True)
                    direct_audio_url = audio_streams[0].get("url")
            
            # אם זה שרת מסוג Invidious API
            elif "adaptiveFormats" in data:
                audio_streams = [f for f in data.get("adaptiveFormats", []) if "audio" in f.get("type", "")]
                if audio_streams:
                    audio_streams.sort(key=lambda x: int(x.get("bitrate", 0)), reverse=True)
                    direct_audio_url = audio_streams[0].get("url")
            
            if direct_audio_url:
                print(f"--- המעקף הצליח! מוריד מזרים ישיר למערכת הפעלה... ---")
                file_res = requests.get(direct_audio_url, timeout=45, stream=True)
                with open(output_path, "wb") as f:
                    for chunk in file_res.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                return True, title
                
        except Exception as e:
            print(f"נקודת קצה {endpoint} נכשלה, עובר אוטומטית לבאה בתור. שגיאה: {e}")
            continue
            
    return False, None

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

    success, title = download_via_global_mesh(target_url, output)
    if success and os.path.exists(output):
        return output_filename, title
        
    raise Exception("כל רשתות הגיבוי העולמיות חסומות כרגע על ידי יוטיוב. נסה שוב מאוחר יותר.")

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
    return send_file(os.path.join(DOWNLOAD_FOLDER, filename), as_attachment=True, mimetype="audio/mpeg")

@app.route("/health")
def health():
    return "OK"

@app.route("/", methods=["GET"])
def home():
    return "Direct Downloader Bot with 100-Steps-Ahead Global Mesh Network is Live!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
