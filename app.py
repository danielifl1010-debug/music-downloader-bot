from flask import Flask, request, jsonify
import yt_dlp
import os
import uuid
import requests

app = Flask(__name__)

DOWNLOAD_FOLDER = 'downloads'
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

def download_song(query):
    file_id = str(uuid.uuid4())
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
            ext = video.get('ext', 'm4a')
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
    
    if not text:
        return jsonify({"hostAppDataAction": {"chatDataAction": {"createMessageAction": {"message": {"text": "אנא שלח שם שיר 🎵"}}}}})

    # 1. הורדת השיר לשרת
    title, filename = download_song(text)
    
    if filename:
        file_path = os.path.join(DOWNLOAD_FOLDER, filename)
        download_url = f"https://music-downloader-bot-7tve.onrender.com/download/{filename}"
        
        # 2. שליחת הודעה עם כרטיסייה (Card) שמכילה כפתור הורדה ישיר ומובנה בתוך גוגל צ'אט
        return jsonify({
            "hostAppDataAction": {
                "chatDataAction": {
                    "createMessageAction": {
                        "message": {
                            "text": f" השיר **{title}** מוכן!",
                            "cardsV2": [{
                                "cardId": "download_card",
                                "card": {
                                    "header": {
                                        "title": title,
                                        "subtitle": "קובץ האודיו מוכן להורדה ישירה",
                                        "imageUrl": "https://fonts.gstatic.com/s/i/short-term/release/googlesymbols/music_note/default/48px.svg"
                                    },
                                    "sections": [{
                                        "widgets": [{
                                            "buttonList": {
                                                "buttons": [{
                                                    "text": "הורד קובץ שמע 📥",
                                                    "onClick": {
                                                        "openLink": {
                                                            "url": download_url
                                                        }
                                                    }
                                                }]
                                            }
                                        }]
                                    }]
                                }
                            }]
                        }
                    }
                }
            }
        })
    else:
        return jsonify({"hostAppDataAction": {"chatDataAction": {"createMessageAction": {"message": {"text": f"נכשלתי בהורדת השיר: '{text}'"}}}}})

@app.route('/download/<filename>', methods=['GET'])
def serve_file(filename):
    return send_from_directory(DOWNLOAD_FOLDER, filename, as_attachment=True)

if __name__ == '__main__':
    app.run(port=10000)
