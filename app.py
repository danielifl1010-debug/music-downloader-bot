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
        folder,
        "--bitrate",
        "192k"
    ]



    try:

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=180
        )


    except subprocess.TimeoutExpired:

        raise Exception(
            "ההורדה לקחה יותר מדי זמן"
        )



    print("===================")
    print("SPOTDL OUTPUT:")
    print(result.stdout)

    print("SPOTDL ERROR:")
    print(result.stderr)

    print("===================")



    if result.returncode != 0:

        raise Exception(
            result.stderr[-500:]
        )



    for root, dirs, files in os.walk(folder):

        for file in files:

            if file.endswith(".mp3"):

                old_path = os.path.join(
                    root,
                    file
                )


                new_path = os.path.join(
                    DOWNLOAD_FOLDER,
                    file
                )


                os.rename(
                    old_path,
                    new_path
                )


                return file



    raise Exception(
        "לא נוצר קובץ MP3"
    )







@app.route("/", methods=["POST"])
def chat():

    try:

        data = request.get_json()


        print("REQUEST:")
        print(data)



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

                "text":
                "❌ לא התקבל שם שיר"

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


        print("ERROR:")
        print(str(e))


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


    if not os.path.exists(path):

        return "File not found", 404



    return send_file(
        path,
        as_attachment=True
    )






@app.route("/health", methods=["GET", "HEAD"])
def health():

    return "OK"






@app.route("/", methods=["GET"])
def home():

    return "Music downloader bot running"






if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=8080
    )
