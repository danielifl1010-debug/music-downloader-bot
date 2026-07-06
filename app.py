from flask import Flask, request, jsonify
import os

app = Flask(__name__)

@app.route("/", methods=["POST"])
def home():
    data = request.get_json()

    print("Payload received:", data)

    user_text = ""

    try:
        user_text = data["messagePayload"]["message"]["argumentText"]
    except Exception:
        user_text = "לא הצלחתי לקרוא את ההודעה"

    return jsonify({
        "text": f"קיבלתי ממך: {user_text}"
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
