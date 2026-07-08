def download_song(query):
    clean_old_files()
    file_id = str(uuid.uuid4())
    output = os.path.join(DOWNLOAD_FOLDER, f"{file_id}.%(ext)s")

    if "youtube.com" not in query and "youtu.be" not in query:
        video_url, video_title = search_youtube_link(query)
        if not video_url:
            raise Exception("לא הצלחתי למצוא תוצאות עבור השיר הזה ביוטיוב.")
        target_url = video_url
    else:
        target_url = query

    options = {
        "format": "ba/ba*",
        "outtmpl": output,
        "noplaylist": True,
        "quiet": False,
        "socket_timeout": 30,
        
        # הגדרה מדויקת ל-OAuth2 דרך הארגומנטים של האקסטרטור כדי למנוע קריסות
        "extractor_args": {
            "youtube": {
                "player_client": ["ios"],
                "skip": ["dash", "hls"],
                "oauth2_scope": "https://www.googleapis.com/auth/youtube"
            }
        },
        "http_headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
    }

    print(f"--- yt-dlp מתחיל הורדה ישירה באמצעות אימות OAuth מהקישור: {target_url} ---")

    try:
        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(target_url, download=True)
            
        if info is None:
            raise Exception("יוטיוב החזיר תשובה ריקה בניסיון ההורדה.")

        title = info.get("title", "שיר")

        files = glob.glob(os.path.join(DOWNLOAD_FOLDER, f"{file_id}.*"))
        if not files:
            raise Exception("הקובץ לא נשמר בשרת הענן.")

        actual_filename = os.path.basename(files[0])
        print(f"--- ההורדה הסתיימה בהצלחה! קובץ נוצר: {actual_filename} ---")
        return actual_filename, title

    except Exception as e:
        print(f"שגיאה בזמן ההורדה של yt-dlp: {e}")
        raise Exception(f"יוטיוב חסם את הזרם. שגיאה: {str(e)[:100]}")
