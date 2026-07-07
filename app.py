from flask import Flask, request, jsonify, send_file
import os
import uuid
import yt_dlp
import glob


app = Flask(__name__)

DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)



def download_song(query):

    file_id = str(uuid.uuid4())

    output = os.path.join(
        DOWNLOAD_FOLDER,
        file_id + ".%(ext)s"
    )


    clients = [
        "web",
        "android",
        "ios"
    ]


    last_error = ""


    for client in clients:

        try:

            print("מנסה client:", client)


            options = {

                "format": "bestaudio/best",

                "outtmpl": output,

                "noplaylist": True,

                "quiet": False,

                "socket_timeout": 30,

                "extractor_args": {
                    "youtube": {
                        "player_client": [
                            client
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


            with yt_dlp.YoutubeDL(options) as ydl:

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


            files = glob.glob(
                DOWNLOAD_FOLDER + "/" + file_id + "*"
            )


            if files:

                return (
                    os.path.basename(files[0]),
                    title
                )


        except Exception as e:

            last_error = str(e)

            print(
                "נכשל:",
                client,
                last_error
            )


    raise Exception(
        "לא הצלחתי להוריד: " + last_error[:200]
    )





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
            "❌ שגיאה:\n" + str(e)

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
