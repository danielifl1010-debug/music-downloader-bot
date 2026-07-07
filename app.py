from flask import Flask, request, jsonify, send_file
import os
import uuid
import yt_dlp


app = Flask(__name__)

DOWNLOAD_FOLDER = "downloads"

os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)


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

        "quiet": False,

        "js_runtimes": {
            "deno": {}
        },

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

        info = ydl.extract_info(
            "ytsearch1:" + query,
            download=True
        )


        if "entries" in info:
            info = info["entries"][0]


        title = info.get(
            "title",
            "שיר"
        )


    return file_id + ".mp3", title



@app.route("/", methods=["POST"])
def chat():

    try:

        data = request.json

        text = ""

        if "chat" in data:
            text = data["chat"]["messagePayload"]["message"]["text"]

        elif "message" in data:
            text = data["message"].get("text","")


        if not text:
            return jsonify({
                "text":"❌ לא קיבלתי שם שיר"
            })


        print("מחפש:", text)


        filename, title = download_song(text)


        url = (
            request.host_url
            +
            "downloads/"
            +
            filename
        )


        return jsonify({

            "text":
            f"🎵 {title}\n\n⬇️ הורדה:\n{url}"

        })


    except Exception as e:

        print("ERROR:", e)

        return jsonify({

            "text":
            "❌ שגיאה:\n" + str(e)[:500]

        })



@app.route("/downloads/<filename>")
def downloads(filename):

    return send_file(
        os.path.join(
            DOWNLOAD_FOLDER,
            filename
        ),
        as_attachment=True
    )



@app.route("/health")
def health():

    return "OK"



@app.route("/", methods=["GET"])
def home():

    return "Bot is running"



if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=8080
    )
