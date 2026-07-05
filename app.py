from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/', methods=['POST'])
def home():
    data = request.get_json()
    
    # הדפסת הנתונים ללוגים של Render כדי שנוכל לראות מה גוגל שולחת
    print("Received data:", data)
    
    if not data:
        return jsonify({"text": "No data received"})
        
    event_type = data.get('type')
    
    # טיפול במצב שבו מוסיפים את הבוט לשיחה או שולחים לו הודעה
    if event_type in ['ADDED_TO_SPACE', 'MESSAGE']:
        user_message = ""
        if 'message' in data and 'text' in data['message']:
            user_message = data['message']['text']
            
        return jsonify({
            "text": f"היי! קיבלתי את ההודעה שלך: '{user_message}'. הבוט מחובר ומגיב בהצלחה!"
        })

    return jsonify({"text": "אירוע התקבל בהצלחה."})

if __name__ == '__main__':
    app.run(port=10000)
