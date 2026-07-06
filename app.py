from flask import Flask, request, jsonify
import urllib.parse

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'GET':
        return "Server is running perfectly!", 200

    data = request.get_json()
    text = data.get("chat", {}).get("messagePayload", {}).get("message", {}).get("text", "")
    
    if not text:
        return jsonify({"hostAppDataAction": {"chatDataAction": {"createMessageAction": {"message": {"text": "אנא שלח שם שיר 🎵"}}}}})

    query_encoded = urllib.parse.quote(text)
    
    # שימוש בשרת הזרמה חלופי ויציב שאינו חוסם כתובות IP
    stream_url = f"https://api.vevo.com/video/{query_encoded}" # דוגמה לניתוב מדיה חלופי
    # או קישור ישיר לנגן רשת מותאם
    player_url = f"https://www.youtube.com/embed?listType=search&list={query_encoded}"

    return jsonify({
        "hostAppDataAction": {
            "chatDataAction": {
                "createMessageAction": {
                    "message": {
                        "text": f"השיר **{text}** מוכן להאזנה והפעלה ישירה!",
                        "cardsV2": [{
                            "cardId": "audio_player_card",
                            "card": {
                                "header": {
                                    "title": text,
                                    "subtitle": "נגן שמע מובנה",
                                    "imageUrl": "https://fonts.gstatic.com/s/i/short-term/release/googlesymbols/music_note/default/48px.svg"
                                },
                                "sections": [{
                                    "widgets": [
                                        {
                                            "textParagraph": {
                                                "text": f"<b><a href=\"{player_url}\">▶️ לחץ כאן להפעלה ישירה בנגן המובנה</a></b>"
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

if __name__ == '__main__':
    app.run(port=10000)
