from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/", methods=["POST"])
def home():
    data = request.get_json()
    print("GOT:", data)

    return jsonify({
        "text": "עובד ✔️"
    }), 200


if __name__ == "__main__":
    app.run()
