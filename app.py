from flask import Flask, request, jsonify, send_from_directory
import yt_dlp
import os
import uuid

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

    title, filename = download_song(text)
    
    if filename:
        # הכתובת הישירה של הקובץ שמזרים את האודיו
        stream_url = f"https://music-downloader-bot-7tve.onrender.com/download/{filename}"
        
        # תגובה המכילה נגן מובנה בתוך חלון השיחה של גוגל צ'אט
        return jsonify({
            "hostAppDataAction": {
                "chatDataAction": {
                    "createMessageAction": {
                        "message": {
                            "text": f"השיר **{title}** מוכן להאזנה ישירה!",
                            "cardsV2": [{
                                "cardId": "audio_player_card",
                                "card": {
                                    "header": {
                                        "title": title,
                                        "subtitle": "לחץ על כפתור ההפעלה להאזנה ישירה",
                                        "imageUrl": "https://fonts.gstatic.com/s/i/short-term/release/googlesymbols/music_note/default/48px.svg"
                                    },
                                    "sections": [{
                                        "widgets": [
                                            {
                                                "textParagraph": {
                                                    "text": f"<a href=\"{stream_url}\">לחץ כאן להפעלה בנגן המובנה 🎧</a>"
                                                }
                                            },
                                            {
                                                "buttonList": {
                                                    "buttons": [{
                                                        "text": "הורדה למחשב 📥",
                                                        "onClick": {
                                                            "openLink": {
                                                                "url": stream_url
                                                            }
                                                        }
                                                    }]
                                                }
                                            }
                                        ]
                                    }]
                                }
                            }]
                        }
                    }
                }
            }
        })
    else:
        return jsonify({"hostAppDataAction": {"chatDataAction": {"createMessageAction": {"message": {"text": f"נכשלתי בעיבוד השיר: '{text}'"}}}}})

@app.route('/download/<filename>', methods=['GET'])
def serve_file(filename):
    # כאן אנחנו מאפשרים גם הזרמה (inline) וגם הורדה
    return send_from_directory(DOWNLOAD_FOLDER, filename, as_attachment=False)

if __name__ == '__main__':
    app.run(port=10000)
