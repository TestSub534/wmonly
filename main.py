import os
import uuid
import subprocess
import asyncio
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    CommandHandler,
    ContextTypes,
    filters
)
from aiohttp import web

# Store video paths per user
user_videos = {}

# Watermark configuration
WATERMARK_TEXT = "Insta / Telegram - @supplywalah"
EMAIL_TEXT = "Supplywalah@proton.me"
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_SIZE = 30
FONT_COLOR = "white"
POSITION = "bottom-right"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send me 2 or more videos, then type /merge to combine them!")

async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    video = await update.message.video.get_file()
    file_path = f"{uuid.uuid4()}.mp4"
    await video.download_to_drive(file_path)

    user_videos.setdefault(user_id, []).append(file_path)
    await update.message.reply_text(f"Video {len(user_videos[user_id])} saved. Send more or type /merge.")

async def apply_watermark(input_path: str, output_path: str):
    position_map = {
        "center": "(w-text_w)/2:(h-text_h)/2",
        "bottom": "(w-text_w)/2:h-text_h-10",
        "bottom-right": "w-text_w-10:h-text_h-10",
        "top-left": "10:10",
        "top-right": "w-text_w-10:10",
    }
    pos = position_map.get(POSITION, "w-text_w-10:h-text_h-10")

    def escape_text(text):
        return text.replace("'", r"\'")

    watermark_escaped = escape_text(WATERMARK_TEXT)
    email_escaped = escape_text(EMAIL_TEXT)

    filter_text = (
        f"drawtext=text='{watermark_escaped}':fontfile='{FONT_PATH}':"
        f"x='{pos.split(':')[0]}':y='{pos.split(':')[1]}':"
        f"fontcolor={FONT_COLOR}:fontsize={FONT_SIZE}:shadowcolor=black:shadowx=2:shadowy=2,"
        f"drawtext=text='{email_escaped}':fontfile='{FONT_PATH}':"
        f"x='(w-text_w)/2':y=10:fontcolor={FONT_COLOR}:fontsize={FONT_SIZE}:shadowcolor=black:shadowx=2:shadowy=2"
    )

    cmd = [
        "ffmpeg",
        "-i", input_path,
        "-vf", filter_text,
        "-codec:a", "copy",
        "-y",
        output_path
    ]

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg watermark error: {stderr.decode()}")

async def merge_videos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    videos = user_videos.get(user_id, [])

    if len(videos) < 2:
        await update.message.reply_text("Please send at least 2 videos before merging.")
        return

    list_file = f"list_{uuid.uuid4()}.txt"
    with open(list_file, "w") as f:
        for path in videos:
            f.write(f"file '{os.path.abspath(path)}'\n")

    merged_path = f"merged_{uuid.uuid4()}.mp4"
    cmd = ["ffmpeg", "-f", "concat", "-safe", "0", "-i", list_file, "-c", "copy", merged_path]
    subprocess.run(cmd, check=True)

    watermarked_path = f"watermarked_{uuid.uuid4()}.mp4"
    await apply_watermark(merged_path, watermarked_path)

    await update.message.reply_video(video=open(watermarked_path, "rb"))

    # Cleanup
    for v in videos:
        os.remove(v)
    os.remove(merged_path)
    os.remove(watermarked_path)
    os.remove(list_file)
    user_videos[user_id] = []

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    for v in user_videos.get(user_id, []):
        if os.path.exists(v):
            os.remove(v)
    user_videos[user_id] = []
    await update.message.reply_text("Your video list has been cleared.")

# Aiohttp healthcheck
async def healthcheck(request):
    return web.Response(text="ok", status=200)

async def start_healthcheck_server():
    port = int(os.environ.get("PORT", 8080))
    app = web.Application()
    app.router.add_get("/", healthcheck)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, port=port)
    print(f"Healthcheck server running on port {port}")
    await site.start()

async def run_polling_bot():
    TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN environment variable not set!")

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("merge", merge_videos))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(MessageHandler(filters.VIDEO, handle_video))

    print("Bot started...")
    await app.run_polling()

async def main():
    await asyncio.gather(
        start_healthcheck_server(),
        run_polling_bot()
    )

if __name__ == "__main__":
    asyncio.run(main())
