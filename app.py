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
    
    # הגדרות מורחבות למניעת חסימות מצד יוטיוב בשרתים מרוחקים
    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'default_search': 'ytsearch',
        'outtmpl': output_template,
        'geo_bypass': True,
        'nocheckcertificate': True,
        'quiet': True,
        'headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
        }
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(query, download=True)
            if 'entries' in info:
                if not info['entries']:
                    return None, None
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
        stream_url = f"https://music-downloader-bot-7tve.onrender.com/download/{filename}"
        
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
                                        "subtitle": "לחץ על הקישור להפעלה בנגן המובנה",
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
        return jsonify({"hostAppDataAction": {"chatDataAction": {"createMessageAction": {"message": {"text": f"מצטער, יוטיוב חסם את הניסיון הנוכחי לעבד את השיר: '{text}'. נסה שוב בעוד רגע."}}}}})

@app.route('/download/<filename>', methods=['GET'])
def serve_file(filename):
    return send_from_directory(DOWNLOAD_FOLDER, filename, as_attachment=False)

if __name__ == '__main__':
    app.run(port=10000)
