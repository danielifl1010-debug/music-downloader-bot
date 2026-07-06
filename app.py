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
    
    # שימוש ב-API הורדות קבוע וישיר שמוצא ומוריד לפי שם השיר באופן אוטומטי
    api_url = f"https://api.vreden.web.id/api/ytmp3?url={requests.utils.quote(query)}"
    
    try:
        print(f"Requesting download link from API for: {query}")
        response = requests.get(api_url, timeout=20)
        
        if response.status_code == 200:
            res_data = response.json()
            result = res_data.get("result", {})
            
            # שליפת הקישור לקובץ ושם השיר
            download_url = result.get("download") if isinstance(result, dict) else res_data.get("url")
            title = result.get("title", "Song") if isinstance(result, dict) else res_data.get("title", "Song")
            
            if download_url:
                print(f"Downloading MP3 file locally from: {download_url}")
                file_response = requests.get(download_url, stream=True, timeout=45)
                if file_response.status_code == 200:
                    with open(file_path, 'wb') as f:
                        for chunk in file_response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    return title, filename
    except Exception as e:
        print(f"Bypass system failed: {e}")
        
    return None, None

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'GET':
        return "Bypass Bot Server is Fixed and Active!", 200

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
        
        # ניסיון העלאה ישירה לצ'אט כקובץ שמע מובנה
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
                print(f"Native attachment failed, falling back to link: {e}")

        # גיבוי: הודעה מעוצבת בצ'אט עם קישור ישיר להורדה
        return jsonify({
            "hostAppDataAction": {
                "chatDataAction": {
                    "createMessageAction": {
                        "message": {
                            "text": f"🎧 השיר **{title}** מוכן! להורדה או האזנה לחץ כאן: {stream_url}"
                        }
                    }
                }
            }
        })
        
    else:
        return jsonify({
            "hostAppDataAction": {
                "chatDataAction": {
                    "createMessageAction": {
                        "message": {
                            "text": f"❌ לא הצלחתי לעבד את השיר '{text}'. נסה שוב בעוד רגע."
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
