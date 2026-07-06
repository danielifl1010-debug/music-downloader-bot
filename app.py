from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/', methods=['POST'])
def home():
    data = request.get_json()
    print("Payload received:", data)
    
    # מבנה הודעה תקני המותאם לשרתי גוגל
    response_payload = {
        "text": "השרת פעיל ומחובר! המערכת זיהתה את ההודעה שלך בהצלחה."
    }
    
    return jsonify(response_payload)

if __name__ == '__main__':
    app.run(port=10000)
