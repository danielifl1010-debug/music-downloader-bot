from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/', methods=['POST'])
def home():
    data = request.get_json()
    print("Google Chat payload:", data)
    
    # החזרת מבנה JSON תקין ומעודכן עבור Google Chat
    return jsonify({
        "text": "השרת מחובר בהצלחה! שלח קישור או שם של שיר כדי שנתחיל לעבוד על ההורדה."
    })

if __name__ == '__main__':
    app.run(port=10000)
