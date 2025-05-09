import random
import html
from datetime import datetime
import humanize
from DarkGod14Bot.modules.sql.clear_cmd_sql import get_clearcmd

from DarkGod14Bot import dispatcher
from DarkGod14Bot.modules.disable import (
    DisableAbleCommandHandler,
    DisableAbleMessageHandler,
)
from DarkGod14Bot.modules.sql import afk_sql as sql
from DarkGod14Bot.modules.users import get_user_id
from DarkGod14Bot.modules.helper_funcs.misc import delete
from telegram import MessageEntity, Update, ParseMode
from telegram.error import BadRequest
from telegram.ext import CallbackContext, Filters, MessageHandler, run_async

AFK_GROUP = 7
AFK_REPLY_GROUP = 8


def afk(update: Update, context: CallbackContext):
    args = update.effective_message.text.split(None, 1)
    user = update.effective_user
    chat = update.effective_chat

    if not user:  # ignore channels
        return

    if user.id in [777000, 1087968824]:
        return

    notice = ""
    if len(args) >= 2:
        reason = args[1]
        if len(reason) > 100:
            reason = reason[:100]
            notice = "\nYour afk reason was shortened to 100 characters."
    else:
        reason = ""

    sql.set_afk(update.effective_user.id, reason)
    fname = update.effective_user.first_name
    try:
        delmsg = update.effective_message.reply_text(
            "{} is now away!{}".format(fname, notice))

        cleartime = get_clearcmd(chat.id, "afk")

        if cleartime:
            context.dispatcher.run_async(delete, delmsg, cleartime.time)

    except BadRequest:
        pass


def no_longer_afk(update: Update, context: CallbackContext):
    user = update.effective_user
    message = update.effective_message
    chat = update.effective_chat

    if not user:  # ignore channels
        return

    res = sql.rm_afk(user.id)
    if res:
        if message.new_chat_members:  # dont say msg
            return
        firstname = update.effective_user.first_name
        try:
            options = [
                "{} is here!",
                "{} is back!",
                "{} is now in the chat!",
                "{} is awake!",
                "{} is back online!",
                "{} is finally here!",
                "Welcome back! {}",
                "Where is {}?\nIn the chat!",
            ]
            chosen_option = random.choice(options)
            delmsg = update.effective_message.reply_text(
                chosen_option.format(firstname))

            cleartime = get_clearcmd(chat.id, "afk")

            if cleartime:
                context.dispatcher.run_async(delete, delmsg, cleartime.time)

        except:
            return


def reply_afk(update: Update, context: CallbackContext):
    bot = context.bot
    message = update.effective_message
    userc = update.effective_user
    userc_id = userc.id
    if message.entities and message.parse_entities(
        [MessageEntity.TEXT_MENTION, MessageEntity.MENTION]
    ):
        entities = message.parse_entities(
            [MessageEntity.TEXT_MENTION, MessageEntity.MENTION]
        )

        chk_users = []
        for ent in entities:
            if ent.type == MessageEntity.TEXT_MENTION:
                user_id = ent.user.id
                fst_name = ent.user.first_name

                if user_id in chk_users:
                    return
                chk_users.append(user_id)

            if ent.type != MessageEntity.MENTION:
                return

            user_id = get_user_id(
                message.text[ent.offset: ent.offset + ent.length])
            if not user_id:
                # Should never happen, since for a user to become AFK they must have spoken. Maybe changed username?
                return

            if user_id in chk_users:
                return
            chk_users.append(user_id)

            try:
                chat = bot.get_chat(user_id)
            except BadRequest:
                print("Error: Could not fetch userid {} for AFK module".format(user_id))
                return
            fst_name = chat.first_name

            check_afk(update, context, user_id, fst_name, userc_id)

    elif message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
        fst_name = message.reply_to_message.from_user.first_name
        check_afk(update, context, user_id, fst_name, userc_id)


def check_afk(update: Update, context: CallbackContext, user_id: int, fst_name: str, userc_id: int):
    chat = update.effective_chat
    if sql.is_afk(user_id):
        user = sql.check_afk_status(user_id)

        if int(userc_id) == int(user_id):
            return

        time = humanize.naturaldelta(datetime.now() - user.time)

        if not user.reason:
            res = f"{fst_name} is *afk*.\nLast seen: `{time} ago`"
        else:
            res = f"{fst_name} is *afk*.\nReason: `{user.reason}`\nLast seen: `{time} ago`"

        delmsg = update.effective_message.reply_text(
        res,
        parse_mode = ParseMode.MARKDOWN,
        )

        cleartime = get_clearcmd(chat.id, "afk")

        if cleartime:
            context.dispatcher.run_async(delete, delmsg, cleartime.time)


def __gdpr__(user_id):
    sql.rm_afk(user_id)


__help__ = """
 • `/afk <reason>`*:* mark yourself as AFK (away from keyboard).
 • `brb <reason>`*:* same as the afk command - but not a command.
When marked as AFK, any mentions will be replied to with a message to say you're not available!
"""

AFK_HANDLER = DisableAbleCommandHandler("afk", afk, run_async=True)
AFK_REGEX_HANDLER = DisableAbleMessageHandler(
    Filters.regex(r"(?i)^brb(.*)$"), afk, friendly="afk"
)
NO_AFK_HANDLER = MessageHandler(Filters.all & Filters.chat_type.groups, no_longer_afk, run_async=True)
AFK_REPLY_HANDLER = MessageHandler(Filters.all & Filters.chat_type.groups, reply_afk, run_async=True)

dispatcher.add_handler(AFK_HANDLER, AFK_GROUP)
dispatcher.add_handler(AFK_REGEX_HANDLER, AFK_GROUP)
dispatcher.add_handler(NO_AFK_HANDLER, AFK_GROUP)
dispatcher.add_handler(AFK_REPLY_HANDLER, AFK_REPLY_GROUP)

__mod_name__ = "AFK"
__command_list__ = ["afk"]
__handlers__ = [
    (AFK_HANDLER, AFK_GROUP),
    (AFK_REGEX_HANDLER, AFK_GROUP),
    (NO_AFK_HANDLER, AFK_GROUP),
    (AFK_REPLY_HANDLER, AFK_REPLY_GROUP),
]
