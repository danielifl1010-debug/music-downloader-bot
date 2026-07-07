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

    filename = file_id + ".mp3"

    filepath = os.path.join(
        DOWNLOAD_FOLDER,
        filename
    )


    options = {

        "format": "bestaudio/best",

        "outtmpl": filepath.replace(
            ".mp3",
            ".%(ext)s"
        ),

        "noplaylist": True,

        "quiet": False,


        "extractor_args": {

            "youtube": {

                "player_client": [
                    "android",
                    "web"
                ]

            }

        },


        "nocheckcertificate": True,


        "ignoreerrors": False,


        "http_headers": {

            "User-Agent":
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120 Safari/537.36"

        },


        "postprocessors": [

            {

                "key": "FFmpegExtractAudio",

                "preferredcodec": "mp3",

                "preferredquality": "192"

            }

        ]

    }



    with yt_dlp.YoutubeDL(options) as ydl:

        result = ydl.extract_info(
            "ytsearch1:" + query,
            download=True
        )


        if "entries" in result:

            title = result["entries"][0]["title"]

        else:

            title = result["title"]



    return filename, title





@app.route("/", methods=["POST"])
def google_chat():

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
            f"❌ שגיאה בהורדה: {str(e)}"

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






@app.route("/health")
def health():

    return "OK"






if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=8080
    )
