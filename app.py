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

def search_youtube_scraped(query):
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        url = f"https://www.youtube.com/results?search_query={requests.utils.quote(query)}"
        res = requests.get(url, headers=headers, timeout=10)
        
        video_ids = re.findall(r"watch\?v=([a-zA-Z0-9_-]{11})", res.text)
        if video_ids:
            return video_ids[0], query
    except Exception as e:
        print(f"Scraper search failed: {e}")
    return None, None

def download_song(query):
    clean_old_files()
    file_id = str(uuid.uuid4())
    filename = f"{file_id}.mp3"
    file_path = os.path.join(DOWNLOAD_FOLDER, filename)
    
    video_id, title = search_youtube_scraped(query)
    
    if not video_id:
        raise Exception("לא הצלחתי לאתר את השיר ביוטיוב. נסה שם אחר.")

    youtube_url = f"https://www.youtube.com/watch?v={video_id}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json"
    }

    # שרת 1: ה-API הרשמי והמרכזי של פרויקט Cobalt (חזק ויציב מאוד)
    # נשתמש ב-Instance הרשמי שמותאם לעומסים
    try:
        print(f"מנסה להוריד משרת המרה מרכזי (Cobalt Official): {youtube_url}")
        payload = {"url": youtube_url, "videoQuality": "720", "audioFormat": "mp3", "isAudioOnly": True}
        # שימוש בשרת חלופי פומבי מוכר של קובלט
        res = requests.post("https://api.cobalt.tools", json=payload, headers=headers, timeout=15)
        if res.status_code == 200 and "url" in res.json():
            dl_url = res.json()["url"]
            print(f"מוריד קובץ משרת 1: {dl_url}")
            file_res = requests.get(dl_url, stream=True, timeout=45)
            if file_res.status_code == 200:
                with open(file_path, 'wb') as f:
                    for chunk in file_res.iter_content(chunk_size=8192):
                        f.write(chunk)
                return filename, title
    except Exception as e:
        print(f"שרת המרה 1 נכשל: {e}")

    # שרת 2: הורדה ישירה של ה-Audio Stream משרתי Piped/Invidious (עוקף לחלוטין את יוטיוב ובטוח ב-100%)
    try:
        print(f"מנסה להוריד stream ישיר משרת גיבוי (Piped API): {video_id}")
        piped_res = requests.get(f"https://pipedapi.kavin.rocks/videos/{video_id}", timeout=15).json()
        
        # מחפש את זרם האודיו בלבד (Audio Streams)
        audio_streams = piped_res.get("audioStreams", [])
        if audio_streams:
            # לוקח את האיכות הטובה ביותר שיש
            dl_url = audio_streams[0].get("url")
            if dl_url:
                print(f"מוריד stream ישיר מ-: {dl_url}")
                file_res = requests.get(dl_url, stream=True, timeout=45)
                if file_res.status_code == 200:
                    with open(file_path, 'wb') as f:
                        for chunk in file_res.iter_content(chunk_size=8192):
                            f.write(chunk)
                    return filename, title
    except Exception as e:
        print(f"שרת המרה 2 נכשל: {e}")

    raise Exception("כל שרתי ההמורה עמוסים או חסמו את הבקשה כרגע. נסה שוב בעוד מספר רגעים.")

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
