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

# המפתח האישי שלך מתוך צילום המסך שהעלית
RAPIDAPI_KEY = "d4a277a3damsh6284a8def8883c3p1e1966jsn5c4606e59304"

def clean_old_files():
    for old_file in glob.glob(DOWNLOAD_FOLDER + "/*"):
        try:
            if time.time() - os.path.getmtime(old_file) > 3600:
                os.remove(old_file)
        except:
            pass

def get_youtube_video_id(query):
    """מוציא את מזהה הוידאו מיוטיוב ללא חסימות"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    # ניסיון 1: בדיקה אם המשתמש שלח ישירות קישור של יוטיוב
    if "youtube.com" in query or "youtu.be" in query:
        found = re.findall(r"(?:v=|\/)([a-zA-Z0-9_-]{11})", query)
        if found:
            return found[0]

    # ניסיון 2: חיפוש טקסטואלי במובייל יוטיוב
    try:
        url = f"https://m.youtube.com/results?search_query={requests.utils.quote(query)}"
        res = requests.get(url, headers=headers, timeout=10)
        video_ids = re.findall(r"\"videoId\":\"([a-zA-Z0-9_-]{11})\"", res.text)
        if video_ids:
            return video_ids[0]
    except Exception as e:
        print(f"חיפוש מובייל נכשל: {e}")

    # ניסיון 3: חיפוש בדסקטופ יוטיוב
    try:
        url = f"https://www.youtube.com/results?search_query={requests.utils.quote(query)}"
        res = requests.get(url, headers=headers, timeout=10)
        video_ids = re.findall(r"watch\?v=([a-zA-Z0-9_-]{11})", res.text)
        if video_ids:
            return video_ids[0]
    except Exception as e:
        print(f"חיפוש דסקטופ נכשל: {e}")

    return None

def download_song(query):
    clean_old_files()
    file_id = str(uuid.uuid4())
    filename = f"{file_id}.mp3"
    file_path = os.path.join(DOWNLOAD_FOLDER, filename)
    
    print(f"מתחיל תהליך איתור עבור השאילתה: {query}")
    video_id = get_youtube_video_id(query)
    
    if not video_id:
        raise Exception("לא הצלחתי למצוא את השיר ביוטיוב. נסה שם אחר או קישור ישיר.")
        
    print(f"נמצא מזהה וידאו: {video_id}. פונה ל-RapidAPI...")

    # פנייה לשרת המרה יציב ומקצועי באמצעות המפתח שלך
    url = "https://youtube-to-mp315.p.rapidapi.com/download"
    querystring = {"id": video_id}
    
    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": "youtube-to-mp315.p.rapidapi.com"
    }

    try:
        response = requests.get(url, headers=headers, params=querystring, timeout=25)
        if response.status_code == 200:
            res_data = response.json()
            dl_url = res_data.get("downloadUrl") or res_data.get("url") or res_data.get("link")
            
            if dl_url:
                print(f"ההמרה הצליחה! מוריד את הקובץ משרת האחסון: {dl_url}")
                file_res = requests.get(dl_url, stream=True, timeout=60)
                if file_res.status_code == 200:
                    with open(file_path, 'wb') as f:
                        for chunk in file_res.iter_content(chunk_size=8192):
                            f.write(chunk)
                    return filename, query
            else:
                print(f"התקבלה תשובה מ-RapidAPI אך ללא לינק תקין: {res_data}")
        else:
            print(f"שגיאת שרת RapidAPI, קוד סטטוס: {response.status_code}")
    except Exception as e:
        print(f"הפנייה ל-RapidAPI נכשלה לחלוטין: {e}")

    raise Exception("שרת ההמורה המקצועי לא זמין כרגע. נסה שוב בעוד דקה.")

@app.route("/", methods=["POST"])
def chat():
    try:
        data = request.get_json() or {}
        text = ""

        # שליפת הטקסט בהתאם למבנה ההודעות שמגיע מהצ'אט שלך
        if "chat" in data:
            text = data["chat"].get("messagePayload", {}).get("message", {}).get("text", "")
        elif "message" in data:
            text = data["message"].get("text", "")
        else:
            text = data.get("text", "")

        if not text:
            return jsonify({"text": "❌ לא התקבל שם שיר או קישור תקין."})

        print(f"התקבלה הודעה בצ'אט: '{text}' - מתחיל הורדה...")
        filename, title = download_song(text)

        # קישור ההורדה ישירות משרת ה-Render שלך
        url = f"https://music-downloader-bot-7tve.onrender.com/downloads/{filename}"

        return jsonify({
            "text": f"🎵 **הורדת השיר הושלמה!**\n\nלחץ על הקישור הבא כדי להוריד:\n{url}"
        })

    except Exception as e:
        print(f"שגיאה כללית באפליקציה: {e}")
        return jsonify({
            "text": f"❌ שגיאה זמנית בהורדת השיר:\n{str(e)[:200]}"
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
    return "Bypass Downloader is live!"

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 10000))
    )
