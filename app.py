from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/', methods=['POST'])
def home():
    data = request.get_json()
    
    # בדיקה שהבקשה מכילה מידע
    if not data:
        return jsonify({"text": "לא התקבל מידע משרתי גוגל."})
        
    # הדפסת ההודעה שהמשתמש שלח לצורך מעקב בלוגים
    user_message = data.get('message', {}).get('text', '')
    print(f"User sent: {user_message}")
    
    # החזרת מבנה תגובה תקין ומלא
    return jsonify({
        "text": f"השרת פעיל ומחובר בהצלחה! הנה מה שכתבת לי: '{user_message}'. בוא נתחיל להגדיר את הורדת השירים האמיתית."
    })

if __name__ == '__main__':
    app.run(port=10000)
