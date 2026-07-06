from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/", methods=["POST"])
def home():
    data = request.get_json()

    text = data.get("chat", {}).get("messagePayload", {}).get("message", {}).get("text", "")
    text_lower = text.lower().strip()

    print("USER:", text)

    # פקודת עזרה
    if text_lower in ["/help", "help"]:
        reply = "כתוב שם של שיר ואני אנסה לטפל בזה 🎵"

    # הודעה רגילה (שם שיר)
    else:
        reply = f"מחפש את: {text} 🔎"

    return jsonify({
        "hostAppDataAction": {
            "chatDataAction": {
                "createMessageAction": {
                    "message": {
                        "text": reply
                    }
                }
            }
        }
    })


if __name__ == "__main__":
    app.run()
