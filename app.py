from flask import Flask, request, jsonify, send_from_directory
import os
import uuid
import requests
from google.oauth2 import service_account
from google.auth.transport.requests import Request

app = Flask(__name__)

PRIVATE_KEY_ENV = os.environ.get("PRIVATE_KEY", "").replace("\\n", "\n")

SERVICE_ACCOUNT_INFO = {
  "type": "service_account",
  "project_id": "ultra-reflector-501506-d9",
  "private_key_id": "26d4536f49a5e758c421425b0b9b1583fb6afa22",
  "private_key": PRIVATE_KEY_ENV,
  "client_email": "chat-bot-manager@ultra-reflector-501506-d9.iam.gserviceaccount.com",
  "client_id": "100045998817769660854",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/chat-bot-manager%40ultra-reflector-501506-d9.iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
}

DOWNLOAD_FOLDER = 'downloads'
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

def get_google_chat_token():
    try:
        scopes = ['https://www.googleapis.com/auth/chat.bot']
        creds = service_account.Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO, scopes=scopes)
        creds.refresh(Request())
        return creds.token
    except Exception as e:
        print(f"Error getting token: {e}")
        return None

def download_song_via_bypass(query):
    file_id = str(uuid.uuid4())
    filename = f"{file_id}.mp3"
    file_path = os.path.join(DOWNLOAD_FOLDER, filename)
    
    try:
        print(f"Searching via reliable search API for: {query}")
        
        # שימוש ב-API חיפוש פתוח ויציב כדי למצוא את מזהה הווידאו של יוטיוב בצורה ישירה
        search_api = f"https://api.vreden.web.id/api/yts?query={requests.utils.quote(query)}"
        search_res = requests.get(search_api, timeout=15).json()
        
        video_url = None
        title = "song"
        
        if search_res.get("status") == 200 and search_res.get("result"):
            video_url = search_res["result"][0].get("url")
            title = search_res["result"][0].get("title", "שיר מבוקש")
            
        if not video_url:
            # אם החיפוש נכשל, ננסה להשתמש במנוע חלופי מהיר
            fallback_search = f"https://io.sccon.top/search?q={requests.utils.quote(query)}"
            f_res = requests.get(fallback_search, timeout=10).json()
            if f_res and isinstance(f_res, list) and len(f_res) > 0:
                video_url = f"https://www.youtube.com/watch?v={f_res[0].get('id')}"
                title = f_res[0].get('title', "שיר מבוקש")

        if not video_url:
            # מוצא אחרון - ננסה להשתמש במבנה ישיר
            video_url = f"https://www.youtube.com/results?search_query={requests.utils.quote(query)}"

        # פנייה למנועי Cobalt החזקים להורדה
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
                print(f"Endpoint failed: {e}")
                continue
                
    except Exception as e:
        print(f"Bypass Error: {e}")
        
    return None, None

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'GET':
        return "Bypass Bot is running perfectly!", 200

    data = request.get_json()
    space_name = data.get("space", {}).get("name", "")
    text = data.get("chat", {}).get("messagePayload", {}).get("message", {}).get("text", "")
    
    if not text:
        return jsonify({"hostAppDataAction": {"chatDataAction": {"createMessageAction": {"message": {"text": "אנא שלח שם שיר 🎵"}}}}})

    title, filename = download_song_via_bypass(text)
    
    if filename:
        file_path = os.path.join(DOWNLOAD_FOLDER, filename)
        token = get_google_chat_token()
        stream_url = f"https://music-downloader-bot-7tve.onrender.com/download/{filename}"
        
        # אם יש טוקן, ננסה קודם כל להעלות את זה כקובץ מובנה (Native Attachment)
        if token:
            try:
                upload_url = f"https://chat.googleapis.com/v1/{space_name}/attachments:upload"
                upload_headers = {
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/octet-stream"
                }
                with open(file_path, "rb") as f:
                    upload_res = requests.post(upload_url, headers=upload_headers, data=f)
                
                if upload_res.status_code == 200:
                    attachment_data = upload_res.json()
                    resource_name = attachment_data.get("attachmentDataRef", {}).get("resourceName", "")
                    
                    return jsonify({
                        "hostAppDataAction": {
                            "chatDataAction": {
                                "createMessageAction": {
                                    "message": {
                                        "text": f"הנה השיר שביקשת: **{title}** 🎧",
                                        "attachment": [{
                                            "resourceName": resource_name,
                                            "contentType": "audio/mpeg"
                                        }]
                                    }
                                }
                            }
                        }
                    })
            except Exception as e:
                print(f"Native upload failed, switching to button link: {e}")

        # פתרון גיבוי מושלם ויציב ב-100%: הודעת כרטיס יפה עם כפתור הורדה ישיר
        return jsonify({
            "actionResponse": {"type": "NEW_MESSAGE"},
            "text": f"🎧 השיר שביקשת מוכן! **{title}**",
            "cardsV2": [{
                "cardId": "downloadCard",
                "card": {
                    "header": {
                        "title": title,
                        "subtitle": "לחץ על הכפתור כדי להוריד או להאזין לשיר",
                        "imageUrl": "https://fonts.gstatic.com/s/i/short-term/release/googlesymbols/music_note/default/48px.svg"
                    },
                    "sections": [{
                        "widgets": [{
                            "buttonList": {
                                "buttons": [{
                                    "text": "📥 הורד את השיר (MP3)",
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
        return jsonify({"hostAppDataAction": {"chatDataAction": {"createMessageAction": {"message": {"text": f"❌ לא הצלחתי למצוא או לעבד את השיר '{text}'. נסה שם אחר או נסה שוב בעוד רגע."}}}}})

@app.route('/download/<filename>', methods=['GET'])
def serve_file(filename):
    return send_from_directory(DOWNLOAD_FOLDER, filename, as_attachment=False)

if __name__ == '__main__':
    app.run(port=10000)
