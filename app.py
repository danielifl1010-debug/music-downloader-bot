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

    output = os.path.join(
        DOWNLOAD_FOLDER,
        file_id + ".%(ext)s"
    )


    ydl_opts = {

        "format": "bestaudio/best",

        "outtmpl": output,

        "noplaylist": True,

        "default_search": "ytsearch1",


        "extractor_args": {
            "youtube": {
                "player_client": [
                    "android"
                ]
            }
        },


        "http_headers": {

            "User-Agent":
            "Mozilla/5.0 (Linux; Android 10)"
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

        info = ydl.extract_info(
            query,
            download=True
        )


        if "entries" in info:

            title = info["entries"][0]["title"]

        else:

            title = info["title"]



    return file_id + ".mp3", title





@app.route("/", methods=["POST"])
def chat_bot():

    try:

        data = request.json


        text = data["chat"]["messagePayload"]["message"]["text"]


        print("מחפש:", text)



        filename, title = download_song(text)



        url = request.host_url + "downloads/" + filename



        return jsonify({

            "text":
            f"🎵 {title}\n\n⬇️ הורדה:\n{url}"

        })


    except Exception as e:


        print("ERROR:", e)


        return jsonify({

            "text":
            f"❌ שגיאה: {str(e)}"

        })






@app.route("/downloads/<filename>")
def download_file(filename):

    path = os.path.join(
        DOWNLOAD_FOLDER,
        filename
    )


    return send_file(
        path,
        as_attachment=True
    )






if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=8080
    )
