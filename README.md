# Telegram Video Merger Bot

A Telegram bot to merge multiple videos and add a watermark.

## Features

- Users send 2+ videos, then type `/merge` to combine them.
- Adds a watermark (social handle + email) to the merged video.
- `/reset` command to clear uploaded videos.

## Requirements

- Python 3.9+
- ffmpeg (must be installed on the system)
- Telegram Bot Token (get from [BotFather](https://t.me/botfather))

## Quick Start (Locally)

1. **Install dependencies**
    ```bash
    pip install -r requirements.txt
    ```

2. **Install ffmpeg**
    - On Ubuntu: `sudo apt-get install ffmpeg`
    - On Mac: `brew install ffmpeg`
    - On Koyeb: Use the Dockerfile below or select a Python runtime with ffmpeg.

3. **Set your bot token**
    ```bash
    export TELEGRAM_BOT_TOKEN=your-bot-token-here
    ```

4. **Run**
    ```bash
    python main.py
    ```

## Deploying on Koyeb

1. Push this repo to GitHub.
2. Create a new "Python" service on Koyeb, connect your repo.
3. Set environment variable: `TELEGRAM_BOT_TOKEN`
4. Ensure ffmpeg is available (use Dockerfile if needed).

## Dockerfile (if you want to use Docker)

```dockerfile
FROM python:3.11-slim

RUN apt-get update && apt-get install -y ffmpeg fonts-dejavu-core && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt

ENV TELEGRAM_BOT_TOKEN=<your-telegram-token>
CMD ["python", "main.py"]
```

## Notes

- Font path for watermark is set to DejaVu Sans, which is commonly available. Change `FONT_PATH` in `main.py` if needed.
- All video/temp files are cleaned after sending the result.
- Don’t commit your Telegram token or video files.

## License

MIT