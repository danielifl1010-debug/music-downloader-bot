from flask import Flask, request, jsonify, send_file
import os
import uuid
import subprocess


app = Flask(__name__)


DOWNLOAD_FOLDER = "downloads"


if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)



def download_song(query):

    file_id = str(uuid.uuid4())

    folder = os.path.join(
        DOWNLOAD_FOLDER,
        file_id
    )

    os.makedirs(folder)



    command = [
        "spotdl",
        "download",
        query,
        "--output",
        folder
    ]


    result = subprocess.run(
        command,
        capture_output=True,
        text=True
    )


    print(result.stdout)
    print(result.stderr)



    mp3_file = None


    for root, dirs, files in os.walk(folder):

        for file in files:

            if file.endswith(".mp3"):

                mp3_file = os.path.join(
                    root,
                    file
                )

                break



    if not mp3_file:

        raise Exception(
            "לא נוצר קובץ MP3"
        )



    filename = os.path.basename(
        mp3_file
    )


    new_path = os.path.join(
        DOWNLOAD_FOLDER,
        filename
    )


    os.rename(
        mp3_file,
        new_path
    )


    return filename





@app.route("/", methods=["POST"])
def chat():

    try:

        data = request.get_json()


        text = ""


        if "chat" in data:

            text = data["chat"]["messagePayload"]["message"]["text"]


        elif "message" in data:

            text = data["message"].get(
                "text",
                ""
            )



        if not text:

            return jsonify({
                "text": "❌ לא התקבל שם שיר"
            })



        print("מחפש:", text)



        filename = download_song(text)



        url = (
            request.host_url
            +
            "downloads/"
            +
            filename
        )



        return jsonify({

            "text":
            f"🎵 מוכן!\n\n⬇️ הורדה:\n{url}"

        })



    except Exception as e:


        print("ERROR:", e)


        return jsonify({

            "text":
            "❌ שגיאה:\n"
            +
            str(e)[:500]

        })






@app.route("/downloads/<filename>")
def download(filename):

    path = os.path.join(
        DOWNLOAD_FOLDER,
        filename
    )


    return send_file(
        path,
        as_attachment=True
    )






@app.route("/health", methods=["GET", "HEAD"])
def health():

    return "OK"






@app.route("/", methods=["GET"])
def home():

    return "Bot running"






if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=8080
    )
