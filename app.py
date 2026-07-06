from flask import Flask, request, jsonify, send_from_directory
import os
import uuid
import requests

app = Flask(__name__)

DOWNLOAD_FOLDER = 'downloads'
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

def download_song_via_cobalt(query):
    file_id = str(uuid.uuid4())
    filename = f"{file_id}.mp3"
    file_path = os.path.join(DOWNLOAD_FOLDER, filename)
    
    try:
        print(f"Searching via open fallback engine for: {query}")
        
        # שלב א': מציאת הקישור מיוטיוב באמצעות מנוע חיפוש פתוח ויציב שאינו נחסם
        search_url = f"https://io.sccon.top/search?q={requests.utils.quote(query)}"
        search_res = requests.get(search_url, timeout=10).json()
        
        video_url = None
        title = query
        
        if search_res and isinstance(search_res, list) and len(search_res) > 0:
            video_url = f"https://www.youtube.com/watch?v={search_res[0].get('id')}"
            title = search_res[0].get('title', query)
        else:
            # מוצא אחרון במידה והחיפוש הישיר נכשל
            video_url = f"https://www.youtube.com/results?search_query={requests.utils.quote(query)}"

        # שלב ב': פנייה ישירה למנוע ההורדות הבינלאומי היציב ביותר (Cobalt)
        cobalt_endpoints = [
            "https://cobalt.tools/api/json",
            "https://api.cobalt.tools/api/json"
        ]
        
        payload = {
            "url": video_url,
            "isAudioOnly": True,
            "audioFormat": "mp3"
        }
        
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        for endpoint in cobalt_endpoints:
            try:
                res = requests.post(endpoint, json=payload, headers=headers, timeout=15)
                if res.status_code == 200:
                    res_data = res.json()
                    dl_url = res_data.get("url")
                    if dl_url:
                        file_res = requests.get(dl_url, stream=True, timeout=45)
                        if file_res.status_code == 200:
                            with open(file_path, 'wb') as f:
                                for chunk in file_res.iter_content(chunk_size=8192):
                                    f.write(chunk)
                            return title, filename
            except Exception as e:
                print(f"Cobalt endpoint failed: {e}")
                continue
                
    except Exception as e:
        print(f"Download processing error: {e}")
        
    return None, None

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'GET':
        return "Music Downloader Bot Server is Live and Clean!", 200

    data = request.get_json()
    text = data.get("chat", {}).get("messagePayload", {}).get("message", {}).get("text", "")
    
    if not text:
        return jsonify({"hostAppDataAction": {"chatDataAction": {"createMessageAction": {"message": {"text": "אנא שלח שם שיר 🎵"}}}}})

    title, filename = download_song_via_cobalt(text)
    
    if filename:
        stream_url = f"https://music-downloader-bot-7tve.onrender.com/download/{filename}"
        
        # החזרת כרטיס לחיץ מעוצב, תקני ויציב ב-100% לתוך גוגל צ'אט
        return jsonify({
            "actionResponse": {"type": "NEW_MESSAGE"},
            "text": f"🎧 השיר שביקשת מוכן!",
            "cardsV2": [{
                "cardId": "downloadCard",
                "card": {
                    "header": {
                        "title": title,
                        "subtitle": "לחץ על הכפתור כדי להאזין או להוריד",
                        "imageUrl": "https://fonts.gstatic.com/s/i/short-term/release/googlesymbols/music_note/default/48px.svg"
                    },
                    "sections": [{
                        "widgets": [{
                            "buttonList": {
                                "buttons": [{
                                    "text": "📥 לחץ להורדת השיר (MP3)",
                                    "onClick": {
                                        "openLink": {
                                            "url": stream_url
                                        }
                                    }
                                }]
                            }
                        }]
                    }]
                }
            }]
        })
    else:
        return jsonify({
            "hostAppDataAction": {
                "chatDataAction": {
                    "createMessageAction": {
                        "message": {
                            "text": f"❌ לא הצלחתי לעבד את השיר '{text}'. אנא נסה שוב בעוד רגע או נסה שם אחר."
                        }
                    }
                }
            }
        })

@app.route('/download/<filename>', methods=['GET'])
def serve_file(filename):
    return send_from_directory(DOWNLOAD_FOLDER, filename, as_attachment=False)

if __name__ == '__main__':
    app.run(port=10000)
