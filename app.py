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
        reply = "כתוב שם של שיר או קישור מיוטיוב, ואני אביא לך קישור חיפוש מהיר 🔎"
    else:
        query_encoded = urllib.parse.quote(text)
        # יצירת קישור ישיר לתוצאות החיפוש ביוטיוב בצורה קלה
        youtube_url = f"https://www.youtube.com/results?search_query={query_encoded}"
        reply = f"הנה קישור ישיר לחיפוש השיר '{text}' ביוטיוב: 🎵\n\n{youtube_url}"

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
