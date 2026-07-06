from flask import Flask, request, jsonify, send_from_directory
import yt_dlp
import os
import uuid
import requests
from google.oauth2 import service_account
from google.auth.transport.requests import Request

app = Flask(__name__)

# קובץ המפתח הרשמי שלך שהתקבל מגוגל קלאוד
SERVICE_ACCOUNT_INFO = {
  "type": "service_account",
  "project_id": "ultra-reflector-501506-d9",
  "private_key_id": "26d4536f49a5e758c421425b0b9b1583fb6afa22",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQDb2lePUNfN8vUv\n91JvSXSQ31vqqoL+py4kkgDXUIiqFwqtav8nn3JC89WCDak2bzKpooTKjy1KjnzZ\njy2itxTgKam3Wmxtjqgnvr9WyfnR1ZV7/I7bsRRgt8k9tfYM80IXOqa+2vm7t98o\n7hRLRdDcA2Zkevs0ycUnf0SxIRxfEW+XNJjJ4BYLea2bqVb6bSnSxIdHISoWkgbm\nP5BUm4kbiVn5Lzv+EEvZHbTs7jfyJiQBkVzJaph1micEp8x4JjrkPbMbNVasOcQw\n1jfkEvw5CfCJCbP/NJ4P/xOYfSqPbx868mTnjLgnPZMVZzrKkkyJXKPxRX5Khot2\nGvjNdCMPAgMBAAECggEAMkXJQ+JOlq951ZAOb5gyaXZJxG1dKvH7oS0puBKYTZyb\nOnB/DAZv0FOFfQm2qdXfld6t0svOpX/TmMQewVhwE5ozTtQEe0DlvsDla+kfkRXv\n6rwjxqTFbiBYih3zt55gfINS4c2c0YoII4ndZiD+03CLl2pvyvBgftmhUYeqvyoG\n31tn/UX9A2E1TWKTkR+eZiww+Z6YjqCVgQy7ChqZMrkET/nmK/aObiA8jC+z7Hqm\nYYP6hNuhchSdePHIZfsmVbE2W3Cb5B3zo8p13af/uoGX1jfXd9d24KVmzXU+TFqR\ngpg5E09AKk5WurRAU8MS6PzV6u51lTtS/73vnHpVUQKBgQD55YgfSbU6/tfNMjgA\nQCR/WZM5PvP1LhL+6TcR4UQKCQCbMkcg8TAxRsootebJ17o+B8uKKK3+r+blp9jU\n4Qk+fGnSAi+HuyXVyMQnWdVdfSQXlr9X79nMZj4FzPvCu2yRuQ6p+XYEdJ7QWtbc\n2XK6Y+ddL+TdRwxmGKn7R30+wwKBgQDhOPaXE3z75JY/sETxIBww4gkbXj8A9Ma1\nJN2mNGGnxleQVFjZLp5CvPzBrSJINfumoWpT5RCKGGnGCJqaZD+6AhdjkEbnj/uk\n2mt7GW3wsA3ZXBJMwmYUy75l/q8oL2vaMD0/q36+d6Ry1Slxli+MeU3M0t0VhbMP\nr6B9tEJdxQKBgQDzBYtpkg7TPr6zaSEY7UgRKRWJ2HT7fUEv8bGCi+XVNIgIZc7S\ndHv/j+5NxQiaRldyt7XzuDfttTcBJEg0TlzlDa0DdOiwQQo8a7CG7FAZSPfukMWo\nSTMwGkY68evspsSguq1OE7H4B0njKlRGFpoCNeHsuAUERHIEX/v+yLk+bQKBgEM7\nqgE3hBv+BQxGJo6Es2W0VFujKtOyPo9czf4LrQtUnlcrlsperEfn+twmPxGna9Q2\nY3Nf8iwHVawUbXKhcpSogyrpqwD9bnWr7mH1GWi8ZaX5Yk0fyzFyEQiJmug4H84m\nkGItY8ygEqtlDtYlq1QX8i2u1OjT3LxWBWcBJL6xAoGBAPIAy9y7HFEr8GXpVyRA\nd29h3X/hangS3ecMkLEV9gawN8jQYB76Aj1ROah6VA8qhYC6dQNBa6PflDlw7xis\nf8CktzFqX3uzRK1hsda1mQbCJYwKdgXSAZG53HYaNVqpPho3IC0hvgyBRX+OSIFN\niSL1H5XWrvSfKSX+v2ajNFUp\n-----END PRIVATE KEY-----\n",
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

# פונקציה שמשיגה מפתח גישה זמני (Token) מגוגל כדי להעלות קבצים לצ'אט
def get_google_chat_token():
    try:
        scopes = ['https://www.googleapis.com/auth/chat.bot']
        creds = service_account.Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO, scopes=scopes)
        creds.refresh(Request())
        return creds.token
    except Exception as e:
        print(f"Error getting token: {e}")
        return None

def download_song(query):
    file_id = str(uuid.uuid4())
    # שימוש בפורמט m4a טבעי של יוטיוב כדי לא להצטרך המרות כבדות שקורסות
    output_template = os.path.join(DOWNLOAD_FOLDER, f"{file_id}.%(ext)s")
    
    ydl_opts = {
        'format': 'bestaudio[ext=m4a]/bestaudio/best',
        'noplaylist': True,
        'default_search': 'ytsearch',
        'outtmpl': output_template,
        'geo_bypass': True,
        'nocheckcertificate': True,
        'quiet': True,
        'headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
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
        return "Server is running perfectly with native attachment support!", 200

    data = request.get_json()
    
    # חילוץ פרטי השיחה כדי לדעת לאיזה חדר/צ'אט להחזיר את הקובץ המצורף
    space_name = data.get("space", {}).get("name", "")
    text = data.get("chat", {}).get("messagePayload", {}).get("message", {}).get("text", "")
    
    if not text:
        return jsonify({"hostAppDataAction": {"chatDataAction": {"createMessageAction": {"message": {"text": "אנא שלח שם שיר 🎵"}}}}})

    title, filename = download_song(text)
    
    if filename:
        file_path = os.path.join(DOWNLOAD_FOLDER, filename)
        token = get_google_chat_token()
        
        if token:
            try:
                # 1. העלאת הקובץ הפיזי לשרתים של גוגל צ'אט (Media Upload)
                upload_url = f"https://chat.googleapis.com/v1/{space_name}/attachments:upload"
                headers = {
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/octet-stream"
                }
                
                with open(file_path, "rb") as f:
                    upload_res = requests.post(upload_url, headers=headers, data=f)
                
                if upload_res.status_code == 200:
                    attachment_data = upload_res.get_json()
                    attachment_resource_name = attachment_data.get("attachmentDataRef", {}).get("resourceName", "")
                    
                    # 2. שליחת הודעה שמכילה את הקובץ המצורף האמיתי (כמו שחבר שולח)
                    return jsonify({
                        "hostAppDataAction": {
                            "chatDataAction": {
                                "createMessageAction": {
                                    "message": {
                                        "text": f"הנה השיר שביקשת: **{title}** 🎧",
                                        "attachment": [{
                                            "resourceName": attachment_resource_name,
                                            "contentType": "audio/mp4"
                                        }]
                                    }
                                }
                            }
                        }
                    })
            except Exception as e:
                print(f"Failed to upload native attachment: {e}")

        # גישת גיבוי במידה והעלאת הקובץ הישירה נכשלה - שליחת קישור הזרמה
        stream_url = f"https://music-downloader-bot-7tve.onrender.com/download/{filename}"
        return jsonify({"hostAppDataAction": {"chatDataAction": {"createMessageAction": {"message": {"text": f"השיר '{title}' מוכן בקישור (העלאה ישירה נכשלה): {stream_url}"}}}}})
        
    else:
        return jsonify({"hostAppDataAction": {"chatDataAction": {"createMessageAction": {"message": {"text": f"מצטער, נכשלתי בעיבוד והורדת השיר: '{text}'"}}}}})

@app.route('/download/<filename>', methods=['GET'])
def serve_file(filename):
    return send_from_directory(DOWNLOAD_FOLDER, filename, as_attachment=False)

if __name__ == '__main__':
    app.run(port=10000)
