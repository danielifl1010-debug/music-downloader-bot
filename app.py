from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/", methods=["POST"])
def home():
    data = request.get_json()
    print(data)

    text = data["chat"]["messagePayload"]["message"]["text"]

    return jsonify({
        "hostAppDataAction": {
            "chatDataAction": {
                "createMessageAction": {
                    "message": {
                        "text": f"קיבלתי: {text}"
                    }
                }
            }
        }
    })
