from flask import Flask, request, jsonify
import yt_dlp
import os
import uuid

app = Flask(__name__)

DOWNLOAD_FOLDER = "downloads"

if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)


def download_song(query):
    file_id = str(uuid.uuid4())

    filename = os.path.join(
        DOWNLOAD_FOLDER,
        file_id + ".mp3"
    )

    options = {
        "format": "bestaudio/best",
        "outtmpl": filename.replace(".mp3", ""),
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
        "noplaylist": True
    }

    with yt_dlp.YoutubeDL(options) as ydl:
        ydl.download([
            f"ytsearch1:{query}"
        ])

    return filename


@app.route("/", methods=["POST"])
def home():

    data = request.get_json()

    print(data)

    try:
        song_name = data["chat"]["messagePayload"]["message"]["text"]

        print("Song:", song_name)

        file_path = download_song(song_name)

        return jsonify({
            "hostAppDataAction": {
                "chatDataAction": {
                    "createMessageAction": {
                        "message": {
                            "text":
                            f"השיר ירד בהצלחה 🎵\nהקובץ נמצא: {file_path}"
                        }
                    }
                }
            }
        })

    except Exception as e:

        print("ERROR:", e)

        return jsonify({
            "hostAppDataAction": {
                "chatDataAction": {
                    "createMessageAction": {
                        "message": {
                            "text":
                            f"שגיאה: {str(e)}"
                        }
                    }
                }
            }
        })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
