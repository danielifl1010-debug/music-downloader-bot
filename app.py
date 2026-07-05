from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/', methods=['POST'])
def home():
    data = request.get_json()
    print("Google Chat Data Received:", data)
    
    # יצירת המבנה המדויק שגוגל צ'אט מצפה לקבל כמענה
    response = {
        "text": "השרת פעיל ומחובר בהצלחה! המערכת מוכנה להמשך פיתוח."
    }
    
    return jsonify(response)

if __name__ == '__main__':
    app.run(port=10000)
