from flask import Flask, request, jsonify
import os

app = Flask(__name__)

@app.route('/', methods=['POST'])
def home():
    event = request.get_json()
    
    # בדיקה האם מדובר באירוע של הודעה מהמשתמש
    if event.get('type') == 'MESSAGE':
        user_message = event.get('message', {}).get('text', '')
        
        # כאן יבוא בהמשך קוד הורדת השירים, כרגע נחזיר תשובת בדיקה:
        reply = f"קיבלתי את ההודעה שלך: '{user_message}'. הבוט בהקמה!"
        
        return jsonify({'text': reply})
        
    return jsonify({})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
