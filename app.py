from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/', methods=['POST'])
def home():
    data = request.get_json()
    
    # בדיקה אם מדובר באירוע הודעה מגוגל צ'אט
    if data and data.get('type') == 'MESSAGE':
        user_message = data['message'].get('text', '')
        return jsonify({
            "text": f"קיבלתי את ההודעה שלך: '{user_message}'. הבוט בהקמה!"
        })
        
    return jsonify({"text": "השרת פעיל, אך לא התקבלה הודעה תקינה."})

if __name__ == '__main__':
    app.run(port=10000)
