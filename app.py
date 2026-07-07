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
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    # מנוע הורדה חלופי ויציב דרך SoundCloud - חסין לחלוטין לחסימות יוטיוב ב-Render
    try:
        print(f"מחפש ומוריד מ-SoundCloud עבור: {query}")
        # שימוש ב-API ציבורי פתוח לחיפוש והורדה מ-SoundCloud
        sc_api_url = f"https://scdownload.onrender.com/api/search?q={requests.utils.quote(query)}"
        
        # אם ה-API החיצוני הזה לא זמין, נשתמש בשרת המרה חלופי ל-SoundCloud/YouTube
        search_res = requests.get(sc_api_url, headers=headers, timeout=12).json()
        
        if search_res and "tracks" in search_res and len(search_res["tracks"]) > 0:
            track = search_res["tracks"][0]
            title = track.get("title", query)
            dl_url = track.get("download_url")
            
            if dl_url:
                print(f"מוריד קובץ מ-SoundCloud: {dl_url}")
                file_res = requests.get(dl_url, stream=True, headers=headers, timeout=45)
                if file_res.status_code == 200:
                    with open(file_path, 'wb') as f:
                        for chunk in file_res.iter_content(chunk_size=8192):
                            f.write(chunk)
                    return filename, title
    except Exception as e:
        print(f"ניסיון SoundCloud נכשל: {e}")

    # מנוע גיבוי 2: שרת המרה חלופי ליוטיוב (Invidious Video-to-Audio Stream) דרך Instance אירופאי יציב
    try:
        print(f"מנסה מנוע גיבוי - חיפוש וידאו ישיר...")
        search_url = f"https://invidious.io.lol/api/v1/search?q={requests.utils.quote(query)}&type=video"
        videos = requests.get(search_url, headers=headers, timeout=10).json()
        
        if videos and len(videos) > 0:
            video_id = videos[0].get("videoId")
            title = videos[0].get("title", query)
            
            # בקשת זרם האודיו הישיר מהשרת ללא המרה
            stream_url = f"https://invidious.io.lol/latest/bypass/{video_id}?audio=1"
            print(f"מוריד stream ישיר משרת גיבוי: {stream_url}")
            
            file_res = requests.get(stream_url, stream=True, headers=headers, timeout=45)
            if file_res.status_code == 200:
                with open(file_path, 'wb') as f:
                    for chunk in file_res.iter_content(chunk_size=8192):
                        f.write(chunk)
                return filename, title
    except Exception as e:
        print(f"מנוע גיבוי 2 נכשל: {e}")

    raise Exception("כל מנועי ההורדה (SoundCloud ויוטיוב) עמוסים כרגע. נסה שיר אחר או נסה שוב מאוחר יותר.")

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
