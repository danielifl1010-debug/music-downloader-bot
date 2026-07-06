from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'GET':
        return "Bot is alive!", 200

    # קבלת המידע מגוגל
    data = request.get_json() or {}
    text = data.get("chat", {}).get("messagePayload", {}).get("message", {}).get("text", "").strip()

    # שליחת תשובה מיידית בפורמט הרשמי של גוגל צ'אט
    return jsonify({
        "text": f"עובד! הנה מה ששלחת לי: {text}\n\nבקרוב נוסיף מחדש את ההורדה הישירה."
    })

if __name__ == '__main__':
    app.run(port=10000)
