import os
import re
import shutil
import tempfile
import time
import threading
import uuid

import yt_dlp
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, Update
from telegram.error import BadRequest, TelegramError
from telegram.ext import CallbackContext, CallbackQueryHandler, run_async

from DarkGod14Bot import dispatcher
from DarkGod14Bot.modules.disable import DisableAbleCommandHandler

YOUTUBE_URL_RE = re.compile(r"(https?://)?(www\.|m\.)?(youtube\.com|youtu\.be)/\S+", re.I)

MAX_VIDEO_MINUTES = 300
MAX_AUDIO_MINUTES = 60
TELEGRAM_UPLOAD_LIMIT_BYTES = 2000 * 1024 * 1024

AUDIO_QUALITIES = [320, 192, 128]

VIDEO_HEIGHT_LABELS = {
    1080: "1080p",
    720: "720p",
    480: "480p",
    360: "360p",
    240: "240p",
}

JOBS = {}
JOBS_LOCK = threading.Lock()
JOB_TTL_SECONDS = 30 * 60


def _new_job(url, owner_id, chat_id):
    job_id = uuid.uuid4().hex[:8]
    with JOBS_LOCK:
        _cleanup_stale_jobs()
        JOBS[job_id] = {
            "url": url,
            "owner_id": owner_id,
            "chat_id": chat_id,
            "created": time.time(),
        }
    return job_id


def _cleanup_stale_jobs():
    now = time.time()
    for jid in [j for j, v in JOBS.items() if now - v["created"] > JOB_TTL_SECONDS]:
        JOBS.pop(jid, None)


def _get_job(job_id):
    with JOBS_LOCK:
        return JOBS.get(job_id)


def _pop_job(job_id):
    with JOBS_LOCK:
        return JOBS.pop(job_id, None)


def extract_info(url):
    opts = {"quiet": True, "no_warnings": True, "skip_download": True}
    with yt_dlp.YoutubeDL(opts) as ydl:
        return ydl.extract_info(url, download=False)


def available_video_heights(info):
    heights = set()
    for f in info.get("formats", []):
        if f.get("vcodec") not in (None, "none") and f.get("height"):
            heights.add(int(f["height"]))
    result = sorted({h for h in VIDEO_HEIGHT_LABELS if h in heights}, reverse=True)
    if not result and heights:
        result = sorted(heights, reverse=True)[:5]
    return result[:5]


def _make_progress_hook(context, chat_id, message_id, state):
    def hook(d):
        if d.get("status") != "downloading":
            return
        total = d.get("total_bytes") or d.get("total_bytes_estimate")
        downloaded = d.get("downloaded_bytes", 0)
        if not total:
            return
        percent = int(downloaded * 100 / total)

        now = time.time()
        if now - state.get("last_edit", 0) < 4 and percent < 100:
            return
        if percent == state.get("last_percent"):
            return

        state["last_percent"] = percent
        state["last_edit"] = now
        bar_filled = percent // 10
        bar = "¦" * bar_filled + "¦" * (10 - bar_filled)
        try:
            context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=f"⬇️ Downloading... {bar} {percent}%",
            )
        except BadRequest:
            pass
        except TelegramError:
            pass

    return hook


def download_video(url, height, tmpdir, progress_hook):
    outtmpl = os.path.join(tmpdir, "%(id)s.%(ext)s")
    fmt = f"bestvideo[height<={height}]+bestaudio/best[height<={height}]"
    opts = {
        "format": fmt,
        "outtmpl": outtmpl,
        "merge_output_format": "mp4",
        "quiet": True,
        "no_warnings": True,
        "progress_hooks": [progress_hook],
        "noplaylist": True,
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info).rsplit(".", 1)[0] + ".mp4", info


def download_audio(url, kbps, tmpdir, progress_hook):
    outtmpl = os.path.join(tmpdir, "%(id)s.%(ext)s")
    opts = {
        "format": "bestaudio/best",
        "outtmpl": outtmpl,
        "quiet": True,
        "no_warnings": True,
        "progress_hooks": [progress_hook],
        "noplaylist": True,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": str(kbps),
            }
        ],
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        base = ydl.prepare_filename(info).rsplit(".", 1)[0]
        return base + ".mp3", info


def find_youtube_link(update: Update, args):
    if args:
        m = YOUTUBE_URL_RE.search(args[0])
        if m:
            return m.group(0)
    reply = update.effective_message.reply_to_message
    if reply and reply.text:
        m = YOUTUBE_URL_RE.search(reply.text)
        if m:
            return m.group(0)
    return None


def youtube_cmd(update: Update, context: CallbackContext):
    message = update.effective_message
    url = find_youtube_link(update, context.args)
    if not url:
        message.reply_text("Usage: /youtube <YouTube link> (or reply to a message containing the link)")
        return

    checking = message.reply_text("🔎 Fetching video information...")
    try:
        info = extract_info(url)
    except yt_dlp.utils.DownloadError:
        checking.edit_text("I could not read that link. Make sure it is a valid YouTube video.")
        return
    except Exception:
        checking.edit_text("An unexpected error occurred while fetching the video information.")
        return

    job_id = _new_job(url, update.effective_user.id, update.effective_chat.id)
    job = _get_job(job_id)
    job["title"] = info.get("title", "?")
    job["duration"] = info.get("duration") or 0
    job["heights"] = available_video_heights(info)

    buttons = [
        [
            InlineKeyboardButton("🎬 Video", callback_data=f"yt|{job_id}|v"),
            InlineKeyboardButton("🎵 Audio", callback_data=f"yt|{job_id}|a"),
        ]
    ]
    duration_min = job["duration"] // 60
    checking.edit_text(
        f"*{info.get('title', '?')}*\nDuration: {duration_min} min\n\nWhat would you like to download?",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(buttons),
    )


def youtube_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    parts = query.data.split("|")
    job_id, action = parts[1], parts[2]

    job = _get_job(job_id)
    if not job:
        query.answer("This menu has expired. Send the link again using /youtube.", show_alert=True)
        return

    if query.from_user.id != job["owner_id"]:
        query.answer("Only the user who requested this video can choose the quality.", show_alert=True)
        return

    query.answer()

    if action == "v":
        if job["duration"] > MAX_VIDEO_MINUTES * 60:
            query.edit_message_text(f"The video is longer than {MAX_VIDEO_MINUTES} minutes and cannot be downloaded as a video.")
            return
        if not job["heights"]:
            query.edit_message_text("No video resolutions were found for this link.")
            return
        buttons = [
            [InlineKeyboardButton(VIDEO_HEIGHT_LABELS.get(h, f"{h}p"), callback_data=f"yt|{job_id}|qv|{h}")]
            for h in job["heights"]
        ]
        query.edit_message_text("Choose the video quality:", reply_markup=InlineKeyboardMarkup(buttons))
        return

    if action == "a":
        if job["duration"] > MAX_AUDIO_MINUTES * 60:
            query.edit_message_text(f"The audio is longer than {MAX_AUDIO_MINUTES} minutes and cannot be downloaded.")
            return
        buttons = [
            [InlineKeyboardButton(f"{kbps} kbps", callback_data=f"yt|{job_id}|qa|{kbps}")]
            for kbps in AUDIO_QUALITIES
        ]
        query.edit_message_text("Choose the audio quality:", reply_markup=InlineKeyboardMarkup(buttons))
        return

    if action in ("qv", "qa"):
        value = parts[3]
        _pop_job(job_id)
        _run_download(context, query, job, action, value)
        return


def _run_download(context, query, job, action, value):
    chat_id = job["chat_id"]
    message_id = query.message.message_id
    url = job["url"]
    tmpdir = tempfile.mkdtemp(prefix="ytdl_")
    state = {"last_percent": -1, "last_edit": 0}
    progress_hook = _make_progress_hook(context, chat_id, message_id, state)

    try:
        query.edit_message_text("⬇️ Downloading... 0%")
        if action == "qv":
            filepath, info = download_video(url, int(value), tmpdir, progress_hook)
            kind = "video"
        else:
            filepath, info = download_audio(url, int(value), tmpdir, progress_hook)
            kind = "audio"

        if not os.path.exists(filepath):
            context.bot.edit_message_text(
                chat_id=chat_id, message_id=message_id,
                text="The download finished, but the final file could not be found. Please try again.",
            )
            return

        size = os.path.getsize(filepath)
        if size > TELEGRAM_UPLOAD_LIMIT_BYTES:
            context.bot.edit_message_text(
                chat_id=chat_id, message_id=message_id,
                text=(
                    f"The file is {size / 1024 / 1024:.1f} MB, but Telegram bots can only upload "
                    f"files up to 50 MB. Please try a lower quality."
                ),
            )
            return

        context.bot.edit_message_text(chat_id=chat_id, message_id=message_id, text="⬆️ Uploading to Telegram...")
        title = info.get("title", "video")
        with open(filepath, "rb") as f:
            if kind == "video":
                context.bot.send_video(
                    chat_id=chat_id, video=f, caption=title,
                    supports_streaming=True, timeout=120,
                )
            else:
                context.bot.send_audio(
                    chat_id=chat_id, audio=f, caption=title,
                    title=title, timeout=120,
                )
        context.bot.delete_message(chat_id=chat_id, message_id=message_id)

    except yt_dlp.utils.DownloadError:
        context.bot.edit_message_text(
            chat_id=chat_id, message_id=message_id,
            text="I could not download that video. It may no longer be available or may be restricted.",
        )
    except TelegramError as e:
        context.bot.edit_message_text(
            chat_id=chat_id, message_id=message_id,
            text=f"The download completed, but the upload to Telegram failed: {e}",
        )
    except Exception:
        context.bot.edit_message_text(
            chat_id=chat_id, message_id=message_id,
            text="An unexpected error occurred during the download.",
        )
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


YOUTUBE_HANDLER = DisableAbleCommandHandler(["youtube", "yt"], youtube_cmd, run_async=True)
YOUTUBE_CALLBACK_HANDLER = CallbackQueryHandler(youtube_callback, pattern=r"^yt\|", run_async=True)

dispatcher.add_handler(YOUTUBE_HANDLER)
dispatcher.add_handler(YOUTUBE_CALLBACK_HANDLER)

__help__ = """
• `/youtube` <link> or `/yt` <link>*:* Download a YouTube video as video or audio, with selectable quality.
"""

__mod_name__ = "YouTube"
__command_list__ = ["youtube", "yt"]
__handlers__ = [YOUTUBE_HANDLER, YOUTUBE_CALLBACK_HANDLER]
