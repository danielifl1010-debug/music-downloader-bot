from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/", methods=["POST"])
def home():
    data = request.get_json()
    print(data)

    return jsonify({
        "actionResponse": {
            "type": "NEW_MESSAGE"
        },
        "cardsV2": [
            {
                "cardId": "1",
                "card": {
                    "sections": [
                        {
                            "widgets": [
                                {
                                    "textParagraph": {
                                        "text": "הבוט עובד 🎉 התחבר בהצלחה ל-Google Chat"
                                    }
                                }
                            ]
                        }
                    ]
                }
            }
        ]
    }) app.run(port=10000)
