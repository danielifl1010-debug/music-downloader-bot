from flask import Flask, request, jsonify, send_from_directory
import yt_dlp
import os
import uuid

app = Flask(__name__)

# יצירת תיקיית הורדות זמנית בשרת
DOWNLOAD_FOLDER = 'downloads'
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

def download_song(query):
    file_id = str(uuid.uuid4())
    # הורדת קובץ האודיו המקורי ללא המרה (חוסך את הצורך ב-FFmpeg ומונע קריסה)
    output_template = os.path.join(DOWNLOAD_FOLDER, f"{file_id}.%(ext)s")
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'default_search': 'ytsearch',
        'outtmpl': output_template,
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(query, download=True)
            if 'entries' in info:
                video = info['entries'][0]
            else:
                video = info
                
            title = video.get('title', 'song')
            ext = video.get('ext', 'm4a')  # חילוץ סיומת הקובץ המקורית
            filename = f"{file_id}.{ext}"
            return title, filename
        except Exception as e:
            print(f"Error downloading song: {e}")
            return None, None

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'GET':
        return "Server is running perfectly!", 200

    data = request.get_json()
    text = data.get("chat", {}).get("messagePayload", {}).get("message", {}).get("text", "")
    text_lower = text.lower().strip()
    
    print("USER:", text)
    
    if not text:
        reply = "אנא שלח לי שם של שיר או קישור מיוטיוב 🎵"
    elif text_lower in ["/help", "help"]:
        reply = "כתוב שם של שיר או קישור מיוטיוב, ואני אוריד לך אותו כקובץ שמע להורדה ישירה 🔎"
    else:
        title, filename = download_song(text)
        
        if filename:
            # הקישור שמוביל לפונקציית ההורדה האוטומטית
            download_url = f"https://music-downloader-bot-7tve.onrender.com/download/{filename}"
            reply = f"השיר '{title}' מוכן! 🎵\n\nלחץ על הקישור הבא וההורדה תתחיל אוטומטית:\n{download_url}"
        else:
            reply = f"מצטער, נכשלתי בהורדת השיר: '{text}'. ודא שהשם תקין."

    return jsonify({
        "hostAppDataAction": {
            "chatDataAction": {
                "createMessageAction": {
                    "message": {
                        "text": reply
                    }
                }
            }
        }
    })

@app.route('/download/<filename>', methods=['GET'])
def serve_file(filename):
    # הפונקציה הזו מכריחה את הדפדפן לבצע הורדה אוטומטית (as_attachment=True)
    return send_from_directory(DOWNLOAD_FOLDER, filename, as_attachment=True)

if __name__ == '__main__':
    app.run(port=10000)
