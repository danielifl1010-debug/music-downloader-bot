from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/', methods=['POST'])
def home():
    data = request.get_json()
    print("Received payload:", data)
    
    # מבנה תשובה רשמי ומלא הכולל את סוג הפעולה
    return jsonify({
        "actionResponse": {
            "type": "NEW_MESSAGE"
        },
        "text": "השרת מחובר ומגיב בצורה תקינה!"
    })

if __name__ == '__main__':
    app.run(port=10000)
