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

def download_song_via_cobalt(query):
    file_id = str(uuid.uuid4())
    filename = f"{file_id}.mp3"
    file_path = os.path.join(DOWNLOAD_FOLDER, filename)
    
    try:
        print(f"Searching and downloading via Cobalt API for: {query}")
        
        # שלב א': שימוש במנוע חיפוש פתוח כדי להמיר את השם של השיר לקישור יוטיוב אמיתי
        search_url = f"https://html.duckduckgo.com/html/?q=site:youtube.com+{requests.utils.quote(query)}"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        search_res = requests.get(search_url, headers=headers, timeout=10)
        
        video_url = None
        if "watch?v=" in search_res.text:
            start_idx = search_res.text.find("watch?v=")
            video_id = search_res.text[start_idx+8:start_idx+19]
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            
        if not video_url:
            # גיבוי קל אם החיפוש נכשל - ננסה להשתמש בקישור ישיר משוער
            video_url = f"https://www.youtube.com/results?search_query={requests.utils.quote(query)}"
            
        # שלב ב': פנייה לשרת ההורדות החזק Cobalt API
        cobalt_urls = [
            "https://cobalt.tools/api/json",
            "https://api.cobalt.tools/api/json"
        ]
        
        payload = {
            "url": video_url,
            "isAudioOnly": True,
            "audioFormat": "mp3",
            "vQuality": "720"
        }
        
        cobalt_headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        for api_endpoint in cobalt_urls:
            try:
                res = requests.post(api_endpoint, json=payload, headers=cobalt_headers, timeout=15)
                if res.status_code == 200:
                    res_data = res.json()
                    download_url = res_data.get("url")
                    title = res_data.get("filename", "song").replace(".mp3", "")
                    
                    if download_url:
                        # הורדת קובץ המוזיקה המוגמר אל השרת שלנו
                        file_response = requests.get(download_url, stream=True, timeout=45)
                        if file_response.status_code == 200:
                            with open(file_path, 'wb') as f:
                                for chunk in file_response.iter_content(chunk_size=8192):
                                    f.write(chunk)
                            return title, filename
            except Exception as e:
                print(f"Endpoint {api_endpoint} failed: {e}")
                continue

    except Exception as e:
        print(f"Cobalt Integration Error: {e}")
    
    return None, None

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'GET':
        return "Bypass Bot Server is fully active with Cobalt Engine!", 200

    data = request.get_json()
    space_name = data.get("space", {}).get("name", "")
    text = data.get("chat", {}).get("messagePayload", {}).get("message", {}).get("text", "")
    
    if not text:
        return jsonify({"hostAppDataAction": {"chatDataAction": {"createMessageAction": {"message": {"text": "אנא שלח שם שיר 🎵"}}}}})

    title, filename = download_song_via_cobalt(text)
    
    if filename:
        file_path = os.path.join(DOWNLOAD_FOLDER, filename)
        token = get_google_chat_token()
        
        if token:
            try:
                upload_url = f"https://chat.googleapis.com/v1/{space_name}/attachments:upload"
                headers = {
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/octet-stream"
                }
                
                with open(file_path, "rb") as f:
                    upload_res = requests.post(upload_url, headers=headers, data=f)
                
                if upload_res.status_code == 200:
                    attachment_data = upload_res.json()
                    attachment_resource_name = attachment_data.get("attachmentDataRef", {}).get("resourceName", "")
                    
                    return jsonify({
                        "hostAppDataAction": {
                            "chatDataAction": {
                                "createMessageAction": {
                                    "message": {
                                        "text": f"הנה השיר שביקשת: **{title}** 🎧",
                                        "attachment": [{
                                            "resourceName": attachment_resource_name,
                                            "contentType": "audio/mpeg"
                                        }]
                                    }
                                }
                            }
                        }
                    })
            except Exception as e:
                print(f"Failed to upload native attachment: {e}")

        stream_url = f"https://music-downloader-bot-7tve.onrender.com/download/{filename}"
        return jsonify({"hostAppDataAction": {"chatDataAction": {"createMessageAction": {"message": {"text": f"השיר '{title}' מוכן להורדה ישירה: {
