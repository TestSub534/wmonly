import os
import uuid
import subprocess
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

user_videos = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("Received /start")
    await update.message.reply_text("Send me 2 or more videos, then type /merge to combine them!")

async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("Received video")
    user_id = update.effective_user.id
    video = await update.message.video.get_file()
    file_path = f"{uuid.uuid4()}.mp4"
    await video.download_to_drive(file_path)

    user_videos.setdefault(user_id, []).append(file_path)
    await update.message.reply_text(f"Video {len(user_videos[user_id])} saved. Send more or type /merge.")

async def merge_videos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("Received /merge")
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
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        await update.message.reply_text("Merging failed.")
        print("FFmpeg error:", e)
        return
    await update.message.reply_video(video=open(merged_path, "rb"))
    # Cleanup
    for v in videos:
        os.remove(v)
    os.remove(merged_path)
    os.remove(list_file)
    user_videos[user_id] = []

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("Received /reset")
    user_id = update.effective_user.id
    for v in user_videos.get(user_id, []):
        if os.path.exists(v):
            os.remove(v)
    user_videos[user_id] = []
    await update.message.reply_text("Your video list has been cleared.")

def main():
    print("Main started")
    TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN environment variable not set!")
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("merge", merge_videos))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(MessageHandler(filters.VIDEO, handle_video))
    print("Bot starting polling...")
    app.run_polling()

if __name__ == "__main__":
    main()v
