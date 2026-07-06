@app.route("/", methods=["POST"])
def home():
    data = request.get_json()

    print(data)

    return {
        "text": "שלום דניאל! הבוט עובד 🎉"
    }, 200
