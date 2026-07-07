from flask import Flask, request, jsonify, send_file
import os
import uuid
import yt_dlp
import glob
import time


app = Flask(__name__)


DOWNLOAD_FOLDER = "downloads"

os.makedirs(
    DOWNLOAD_FOLDER,
    exist_ok=True
)



def clean_old_files():

    for old_file in glob.glob(DOWNLOAD_FOLDER + "/*"):

        try:

            if time.time() - os.path.getmtime(old_file) > 3600:

                os.remove(old_file)

        except:

            pass




def download_song(query):

    clean_old_files()


    file_id = str(uuid.uuid4())


    output = os.path.join(
        DOWNLOAD_FOLDER,
        file_id + ".%(ext)s"
    )


    clients = [
        "android",
        "ios",
        "web"
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


                "nocheckcertificate": True,


                "geo_bypass": True,


                "http_headers": {

                    "User-Agent":
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"

                },


                "extractor_args": {

                    "youtube": {

                        "player_client": [
                            client
                        ]

                    }

                },


                "postprocessors": [

                    {

                        "key":
                        "FFmpegExtractAudio",

                        "preferredcodec":
                        "mp3",

                        "preferredquality":
                        "192"

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
                DOWNLOAD_FOLDER
                +
                "/"
                +
                file_id
                +
                "*"
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
        "לא הצלחתי להוריד: "
        +
        last_error[:300]
    )





@app.route("/", methods=["POST"])
def chat():


    try:


        data = request.json or {}


        text = ""



        if "chat" in data:


            text = (
                data["chat"]
                ["messagePayload"]
                ["message"]
                ["text"]
            )



        elif "message" in data:


            text = data["message"].get(
                "text",
                ""
            )



        if not text:


            return jsonify({

                "text":
                "❌ לא קיבלתי שם שיר"

            })



        print(
            "מחפש להוריד:",
            text
        )



        filename, title = download_song(text)



        url = (

            "https://"
            +
            request.host
            +
            "/downloads/"
            +
            filename

        )



        return jsonify({


            "text":

            f"🎵 {title}\n\n⬇️ הורדה:\n{url}"


        })



    except Exception as e:



        print(
            "ERROR:",
            e
        )



        return jsonify({

            "text":
            "❌ שגיאה:\n"
            +
            str(e)[:500]

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

        port=int(
            os.environ.get(
                "PORT",
                10000
            )
        )

    )
