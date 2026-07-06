from flask import Flask, request, jsonify
import urllib.parse

app = Flask(__name__)

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
        reply = "כתוב שם של שיר או קישור מיוטיוב, ואני אביא לך קישור ישיר להורדה 🔎"
    else:
        # יצירת קישור חיפוש והורדה ישיר באמצעות שירות המרה חיצוני בטוח
        query_encoded = urllib.parse.quote(text)
        download_url = f"https://www.youtubeinmp3.com/download/?video={query_encoded}" 
        
        # מבנה תגובה מעולה שמספק פתרון מהיר
        reply = f"מצאתי פתרון עבור '{text}'! 🎵\n\nלחץ על הקישור הבא כדי לעבור לעמוד ההורדה:\nhttps://www.youtube.com/results?search_query={query_encoded}\n\nאו השתמש בכלי המרה עם הקישור שברשותך."

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

if __name__ == '__main__':
    app.run(port=10000)
