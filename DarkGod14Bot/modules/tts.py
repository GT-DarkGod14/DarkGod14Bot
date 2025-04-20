import uuid
import os
from datetime import datetime
from typing import List
from gtts import gTTS
from gtts.tts import gTTSError
from telegram import Update, ChatAction, ParseMode

from DarkGod14Bot.modules.sql.clear_cmd_sql import get_clearcmd
from DarkGod14Bot import dispatcher
from telegram.ext import CallbackContext, CommandHandler, run_async
from DarkGod14Bot.modules.disable import DisableAbleCommandHandler
from DarkGod14Bot.modules.helper_funcs.misc import delete


def tts(update: Update, context: CallbackContext):
    message = update.effective_message
    chat = update.effective_chat
    args = context.args
    delmsg = None

    text = ""
    if message.reply_to_message:
        text = message.reply_to_message.text or message.reply_to_message.caption or ""
    elif args:
        text = "  ".join(args).lower()
    else:
        message.reply_text(
            "Reply to a message or use: /tts <message>",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    if not text.strip():
        message.reply_text("Please provide valid text to convert to speech.")
        return

    filename = f"tts_{uuid.uuid4()}.mp3"

    try:
        message.chat.send_action(ChatAction.RECORD_AUDIO)

        tts = gTTS(text=text, lang='en', tld='com')
        tts.save(filename)

        with open(filename, 'rb') as audio_file:
            delmsg = message.reply_voice(
                voice=audio_file,
                quote=False
            )

        cleartime = get_clearcmd(chat.id, "tts")

        if cleartime:
            context.dispatcher.run_async(delete, delmsg, cleartime.time)

    except Exception as e:
        message.reply_text(f"Failed to connect to the TTS service: {e}")

    try:
        os.remove(filename)
    except:
        pass

TTS_HANDLER = DisableAbleCommandHandler("tts", tts, run_async=True)
dispatcher.add_handler(TTS_HANDLER)

__handlers__ = [TTS_HANDLER]
