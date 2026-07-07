from flask import Flask, request, jsonify
import yt_dlp
import os
import uuid

app = Flask(__name__)


DOWNLOAD_FOLDER = "downloads"

if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)


def download_song(search):

    file_id = str(uuid.uuid4())

    output = os.path.join(
        DOWNLOAD_FOLDER,
        file_id + ".%(ext)s"
    )

    options = {
        "format": "bestaudio/best",
        "outtmpl": output,
        "noplaylist": True,

        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192"
            }
        ]
    }


    with yt_dlp.YoutubeDL(options) as ydl:

        info = ydl.extract_info(
            f"ytsearch1:{search}",
            download=True
        )

        title = info["entries"][0]["title"]


    return file_id + ".mp3", title



@app.route("/", methods=["POST"])
def chat_bot():

    data = request.json

    try:

        text = data["chat"]["messagePayload"]["message"]["text"]

        print("מחפש:", text)


        filename, title = download_song(text)


        url = request.host_url + "downloads/" + filename


        return jsonify({

            "text":
            f"🎵 מצאתי:\n{title}\n\nהורדה:\n{url}"

        })


    except Exception as e:

        print(e)

        return jsonify({

            "text":
            "❌ הייתה שגיאה בהורדת השיר"

        })


@app.route("/downloads/<file>")
def files(file):

    return open(
        os.path.join(DOWNLOAD_FOLDER,file),
        "rb"
    ).read()



if __name__ == "__main__":
    app.run(host="0.0.0.0",port=8080)
