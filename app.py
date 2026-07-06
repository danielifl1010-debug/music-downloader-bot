from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def home():
    # תמיכה גם בבקשות GET (בשביל המוניטור של UptimeRobot)
    if request.method == 'GET':
        return "Server is running!", 200

    # טיפול בבקשות POST של גוגל צ'אט
    data = request.get_json()
    print("Google Chat Data:", data)

    # מבנה תגובה פשוט וישיר שגוגל מאשרת
    return jsonify({
        "text": "הבדיקה הצליחה! השרת מחובר ומגיב בהצלחה."
    })

if __name__ == '__main__':
    app.run(port=10000)
