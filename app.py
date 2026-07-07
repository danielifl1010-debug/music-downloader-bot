from flask import Flask, request, jsonify, send_file
import yt_dlp
import os
import uuid


app = Flask(__name__)


DOWNLOAD_FOLDER = "downloads"


if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)



def download_song(query):

    file_id = str(uuid.uuid4())

    output_template = os.path.join(
        DOWNLOAD_FOLDER,
        file_id + ".%(ext)s"
    )


    ydl_opts = {

        "format": "bestaudio/best",

        "outtmpl": output_template,

        "noplaylist": True,

        "quiet": False,

        "no_warnings": False,

        "extractor_args": {
            "youtube": {
                "player_client": [
                    "android"
                ]
            }
        },


        "postprocessors": [

            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192"
            }

        ]

    }



    with yt_dlp.YoutubeDL(ydl_opts) as ydl:

        result = ydl.extract_info(
            "ytsearch1:" + query,
            download=True
        )


        entries = result.get(
            "entries",
            []
        )


        if not entries:

            raise Exception(
                "לא נמצאו תוצאות לשיר הזה"
            )


        title = entries[0].get(
            "title",
            "Unknown"
        )


    filename = file_id + ".mp3"


    return filename, title





@app.route("/", methods=["POST"])
def google_chat():

    try:

        data = request.get_json()


        print("Google request:")
        print(data)



        # תמיכה בפורמט Google Chat החדש
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



        filename, title = download_song(text)



        url = request.host_url + "downloads/" + filename



        return jsonify({

            "text":
            f"🎵 {title}\n\n⬇️ הורדה:\n{url}"

        })



    except Exception as e:


        print("ERROR:")
        print(str(e))


        return jsonify({

            "text":
            "❌ שגיאה:\n\n"
            + str(e)[:500]

        })






@app.route("/downloads/<filename>")
def downloads(filename):

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

    return "Music downloader bot is running"






if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=8080
    )
