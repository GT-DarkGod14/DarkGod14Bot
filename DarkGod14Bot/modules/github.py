import html
from typing import Optional, List
import schedule
import time
import threading
import requests

import DarkGod14Bot.modules.helper_funcs.git_api as api
import DarkGod14Bot.modules.sql.github_sql as sql

from DarkGod14Bot.modules.sql.clear_cmd_sql import get_clearcmd
from DarkGod14Bot import dispatcher, OWNER_ID, EVENT_LOGS, SUDO_USERS, SUPPORT_USERS
from DarkGod14Bot.modules.helper_funcs.filters import CustomFilters
from DarkGod14Bot.modules.helper_funcs.chat_status import user_admin
from DarkGod14Bot.modules.helper_funcs.misc import delete
from DarkGod14Bot.modules.disable import DisableAbleCommandHandler

from telegram.ext import (
    CallbackContext,
    CommandHandler,
    Filters,
    MessageHandler,
    RegexHandler,
    run_async,
)

from telegram import (
    Message,
    Chat,
    Update,
    Bot,
    User,
    ParseMode,
    InlineKeyboardMarkup,
    MAX_MESSAGE_LENGTH,
)


def get_latest_commit(repo_url):
    """Get the latest commit from a repository"""
    try:
        if repo_url.startswith("https://github.com/"):
            repo_path = repo_url.replace("https://github.com/", "")
        else:
            repo_path = repo_url

        api_url = f"https://api.github.com/repos/{repo_path}/commits"
        response = requests.get(api_url)

        if response.status_code == 200:
            commits = response.json()
            if commits:
                latest = commits[0]
                return {
                    "sha": latest["sha"],
                    "message": latest["commit"]["message"],
                    "author": latest["commit"]["author"]["name"],
                    "date": latest["commit"]["author"]["date"],
                    "url": latest["html_url"],
                }
    except Exception as e:
        print(f"Error getting commits from {repo_url}: {e}")
    return None


def format_commit_notification(commit_data, repo_name):
    """Format the commit notification message"""
    author = commit_data["author"]
    message_lines = commit_data["message"].split("\n")
    commit_title = message_lines[0]  # First line of commit
    commit_id = commit_data["sha"][:7]  # First 7 characters of SHA
    url = commit_data["url"]

    text = f"🔄 <b>New update in {repo_name}</b>\n\n"
    text += f"👤 <b>Author:</b> {author}\n"
    text += f"📝 <b>Commit:</b> <code>{commit_id}</code>\n"
    text += f"💬 <b>Message:</b> {commit_title}\n"
    text += f"🔗 <a href='{url}'>View full commit</a>"

    return text


def check_repo_updates():
    """Check for updates in all monitored repositories"""
    try:
        monitored_repos = (
            sql.get_all_monitored_repos()
        )  # Need to add this function to SQL

        for repo_data in monitored_repos:
            chat_id = repo_data.chat_id
            repo_url = repo_data.repo_url
            repo_name = repo_data.repo_name
            last_commit_sha = repo_data.last_commit_sha

            latest_commit = get_latest_commit(repo_url)

            if latest_commit and latest_commit["sha"] != last_commit_sha:
                message = format_commit_notification(latest_commit, repo_name)

                try:
                    dispatcher.bot.send_message(
                        chat_id=chat_id,
                        text=message,
                        parse_mode=ParseMode.HTML,
                        disable_web_page_preview=False,
                    )

                    sql.update_last_commit(chat_id, repo_name, latest_commit["sha"])

                    print(f"Notification sent for {repo_name} to chat {chat_id}")

                except Exception as e:
                    print(f"Error sending notification to {chat_id}: {e}")

    except Exception as e:
        print(f"Error checking for updates: {e}")


def start_monitor():
    """Start repository monitoring"""
    schedule.every(5).minutes.do(check_repo_updates)

    def run_scheduler():
        while True:
            schedule.run_pending()
            time.sleep(1)

    monitor_thread = threading.Thread(target=run_scheduler, daemon=True)
    monitor_thread.start()
    print("Repository monitor started - checking every 5 minutes")


@user_admin
def add_monitor(update: Update, context: CallbackContext):
    """Add a repository to monitor"""
    bot, args = context.bot, context.args
    chat_id = update.effective_chat.id
    msg = update.effective_message

    if len(args) < 2:
        deletion(
            update,
            context,
            msg.reply_text(
                "❌ Incorrect usage\n"
                "Use: <code>/monitor &lt;name&gt; &lt;user/repo or URL&gt;</code>\n\n"
                "Examples:\n"
                "• <code>/monitor MyBot user/my-bot</code>\n"
                "• <code>/monitor MyBot https://github.com/user/my-bot</code>",
                parse_mode=ParseMode.HTML,
            ),
        )
        return

    repo_name = args[0]
    repo_input = args[1]

    if repo_input.startswith("https://github.com/"):
        repo_url = repo_input.replace("https://github.com/", "")
    else:
        repo_url = repo_input

    latest_commit = get_latest_commit(repo_url)
    if not latest_commit:
        deletion(
            update,
            context,
            msg.reply_text(
                f"❌ Could not access repository: <code>{repo_url}</code>\n"
                "Please verify that the repository exists and is public.",
                parse_mode=ParseMode.HTML,
            ),
        )
        return

    success = sql.add_monitored_repo(
        str(chat_id), repo_name, repo_url, latest_commit["sha"]
    )

    if success:
        deletion(
            update,
            context,
            msg.reply_text(
                f"✅ <b>Repository added to monitoring!</b>\n\n"
                f"📁 <b>Name:</b> {repo_name}\n"
                f"🔗 <b>Repo:</b> <code>{repo_url}</code>\n\n"
                f"You'll receive automatic notifications when there are new commits.",
                parse_mode=ParseMode.HTML,
            ),
        )
    else:
        deletion(
            update,
            context,
            msg.reply_text(
                "❌ Error adding repository. It might already exist with that name.",
                parse_mode=ParseMode.HTML,
            ),
        )


@user_admin
def remove_monitor(update: Update, context: CallbackContext):
    """Remove a repository from monitoring"""
    bot, args = context.bot, context.args
    chat_id = update.effective_chat.id
    msg = update.effective_message

    if len(args) != 1:
        deletion(
            update,
            context,
            msg.reply_text(
                "❌ Usage: <code>/unmonitor &lt;name&gt;</code>",
                parse_mode=ParseMode.HTML,
            ),
        )
        return

    repo_name = args[0]
    success = sql.remove_monitored_repo(str(chat_id), repo_name)

    if success:
        deletion(
            update,
            context,
            msg.reply_text(
                f"✅ Repository <b>{repo_name}</b> removed from monitoring.",
                parse_mode=ParseMode.HTML,
            ),
        )
    else:
        deletion(
            update,
            context,
            msg.reply_text(
                f"❌ No repository found with the name <b>{repo_name}</b>.",
                parse_mode=ParseMode.HTML,
            ),
        )


def list_monitored(update: Update, context: CallbackContext):
    """List monitored repositories"""
    chat_id = update.effective_chat.id
    chat = update.effective_chat
    chat_name = chat.title or chat.first_name or chat.username

    monitored_list = sql.get_monitored_repos_by_chat(str(chat_id))

    if not monitored_list:
        deletion(
            update,
            context,
            update.effective_message.reply_text(
                "📭 No repositories are being monitored in this chat.\n\n"
                "Use <code>/monitor &lt;name&gt; &lt;user/repo&gt;</code> to add one.",
                parse_mode=ParseMode.HTML,
            ),
        )
        return

    msg = f"📋 <b>Monitored repositories in {chat_name}:</b>\n\n"

    for repo in monitored_list:
        msg += f"📁 <b>{repo.repo_name}</b>\n"
        msg += f"   🔗 <code>{repo.repo_url}</code>\n"
        msg += f"   🔄 Last check: <code>{repo.last_commit_sha[:7] if repo.last_commit_sha else 'N/A'}</code>\n\n"

    msg += "<i>💡 Tip: Use /unmonitor &lt;name&gt; to remove a repo from monitoring</i>"

    deletion(
        update,
        context,
        update.effective_message.reply_text(msg, parse_mode=ParseMode.HTML),
    )


def force_check(update: Update, context: CallbackContext):
    """Force check for updates"""
    msg = update.effective_message
    deletion(update, context, msg.reply_text("🔄 Checking for updates..."))

    check_repo_updates()

    deletion(update, context, msg.reply_text("✅ Check completed!"))


def getphh(index):
    recentRelease = api.getReleaseData(
        api.getData("TrebleDroid/treble_experimentations"), index
    )
    if recentRelease is None:
        return "The specified release could not be found"
    author = api.getAuthor(recentRelease)
    authorUrl = api.getAuthorUrl(recentRelease)
    name = api.getReleaseName(recentRelease)
    assets = api.getAssets(recentRelease)
    releaseName = api.getReleaseName(recentRelease)
    message = "<b>Author:</b> <a href='{}'>{}</a>\n".format(authorUrl, author)
    message += "<b>Release Name:</b> <code>" + releaseName + "</code>\n\n"
    message += "<b>Assets:</b>\n"
    for asset in assets:
        fileName = api.getReleaseFileName(asset)
        if fileName in ("manifest.xml", "patches.zip"):
            continue
        fileURL = api.getReleaseFileURL(asset)
        assetFile = "• <a href='{}'>{}</a>".format(fileURL, fileName)
        sizeB = ((api.getSize(asset)) / 1024) / 1024
        size = "{0:.2f}".format(sizeB)
        message += assetFile + "\n"
        message += "    <code>Size: " + size + " MB</code>\n"
    return message


# do not async
def getData(url, index):
    if not api.getData(url):
        return "Invalid <user>/<repo> combo.\nAre you sure this repository has a release file?"
    recentRelease = api.getReleaseData(api.getData(url), index)
    if recentRelease is None:
        return "The specified release could not be found"
    author = api.getAuthor(recentRelease)
    authorUrl = api.getAuthorUrl(recentRelease)
    name = api.getReleaseName(recentRelease)
    assets = api.getAssets(recentRelease)
    releaseName = api.getReleaseName(recentRelease)
    message = "*Author:* [{}]({})\n".format(author, authorUrl)
    message += "*Release Name:* " + releaseName + "\n\n"
    for asset in assets:
        message += "*Asset:* \n"
        fileName = api.getReleaseFileName(asset)
        fileURL = api.getReleaseFileURL(asset)
        assetFile = "[{}]({})".format(fileName, fileURL)
        sizeB = ((api.getSize(asset)) / 1024) / 1024
        size = "{0:.2f}".format(sizeB)
        downloadCount = api.getDownloadCount(asset)
        message += assetFile + "\n"
        message += "Size: " + size + " MB"
        message += "\nDownload Count: " + str(downloadCount) + "\n\n"
    return message


# likewise, aux function, not async
def getRepo(bot, update, reponame):
    chat_id = update.effective_chat.id
    repo = sql.get_repo(str(chat_id), reponame)
    if repo:
        return repo.value, repo.backoffset
    return None, None


def getRelease(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    msg = update.effective_message
    if len(args) == 0:
        msg.reply_text("Please use some arguments!")
        return
    if (
        len(args) != 1
        and not (len(args) == 2 and args[1].isdigit())
        and not ("/" in args[0])
    ):
        deletion(
            update,
            context,
            msg.reply_text("Please specify a valid combination of <user>/<repo>"),
        )
        return
    index = 0
    if len(args) == 2:
        index = int(args[1])
    url = args[0]
    text = getData(url, index)
    deletion(
        update,
        context,
        msg.reply_text(
            text, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True
        ),
    )
    return


def hashFetch(update: Update, context: CallbackContext):  # kanged from notes
    bot, args = context.bot, context.args
    message = update.effective_message.text
    msg = update.effective_message
    fst_word = message.split()[0]
    no_hash = fst_word[1:]
    url, index = getRepo(bot, update, no_hash)
    if url is None and index is None:
        deletion(
            update,
            context,
            msg.reply_text(
                "There was a problem parsing your request. Likely this is not a saved repo shortcut",
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True,
            ),
        )
        return
    text = getData(url, index)
    deletion(
        update,
        context,
        msg.reply_text(
            text, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True
        ),
    )
    return


def cmdFetch(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    msg = update.effective_message
    if len(args) != 1:
        deletion(update, context, msg.reply_text("Invalid repo name"))
        return
    url, index = getRepo(bot, update, args[0])
    if url is None and index is None:
        deletion(
            update,
            context,
            msg.reply_text(
                "There was a problem parsing your request. Likely this is not a saved repo shortcut",
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True,
            ),
        )
        return
    text = getData(url, index)
    deletion(
        update,
        context,
        msg.reply_text(
            text, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True
        ),
    )
    return


def changelog(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    msg = update.effective_message
    if len(args) != 1:
        deletion(update, context, msg.reply_text("Invalid repo name"))
        return
    url, index = getRepo(bot, update, args[0])
    if not api.getData(url):
        msg.reply_text("Invalid <user>/<repo> combo")
        return
    data = api.getData(url)
    release = api.getReleaseData(data, index)
    body = api.getBody(release)
    deletion(update, context, msg.reply_text(body))
    return


@user_admin
def saveRepo(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    chat_id = update.effective_chat.id
    msg = update.effective_message
    if (
        len(args) != 2
        and (len(args) != 3 and not args[2].isdigit())
        or not ("/" in args[1])
    ):
        deletion(
            update,
            context,
            msg.reply_text(
                "Invalid data, use <reponame> <user>/<repo> <value (optional)>"
            ),
        )
        return
    index = 0
    if len(args) == 3:
        index = int(args[2])
    sql.add_repo_to_db(str(chat_id), args[0], args[1], index)
    deletion(update, context, msg.reply_text("Repo shortcut saved successfully!"))
    return


@user_admin
def delRepo(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    chat_id = update.effective_chat.id
    msg = update.effective_message
    if len(args) != 1:
        msg.reply_text("Invalid repo name!")
        return
    sql.rm_repo(str(chat_id), args[0])
    deletion(update, context, msg.reply_text("Repo shortcut deleted successfully!"))
    return


def listRepo(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    chat = update.effective_chat
    chat_name = chat.title or chat.first_name or chat.username
    repo_list = sql.get_all_repos(str(chat_id))
    msg = "*List of repo shortcuts in {}:*\n"
    des = "You can get repo shortcuts by using `/fetch repo`, or `&repo`.\n"
    for repo in repo_list:
        repo_name = " • `{}`\n".format(repo.name)
        if len(msg) + len(repo_name) > MAX_MESSAGE_LENGTH:
            deletion(
                update,
                context,
                update.effective_message.reply_text(msg, parse_mode=ParseMode.MARKDOWN),
            )
            msg = ""
        msg += repo_name
    if msg == "*List of repo shortcuts in {}:*\n":
        deletion(
            update,
            context,
            update.effective_message.reply_text("No repo shortcuts in this chat!"),
        )
    elif len(msg) != 0:
        deletion(
            update,
            context,
            update.effective_message.reply_text(
                msg.format(chat_name) + des, parse_mode=ParseMode.MARKDOWN
            ),
        )


def getVer(update: Update, context: CallbackContext):
    msg = update.effective_message
    ver = api.vercheck()
    deletion(update, context, msg.reply_text("GitHub API version: " + ver))
    return


def deletion(update: Update, context: CallbackContext, delmsg):
    chat = update.effective_chat
    cleartime = get_clearcmd(chat.id, "github")

    if cleartime:
        context.dispatcher.run_async(delete, delmsg, cleartime.time)


__help__ = """
*Github module. This module will fetch github releases and monitor repositories for updates*\n
*Available commands:*
 • `/git <user>/<repo>`: will fetch the most recent release from that repo.
 • `/git <user>/<repo> <number>`: will fetch releases in past.
 • `/fetch <reponame> or &reponame`: same as `/git`, but you can use a saved repo shortcut
 • `/listrepo`: lists all repo shortcuts in chat
 • `/gitver`: returns the current API version
 • `/changelog <reponame>`: gets the changelog of a saved repo shortcut

*Repository Monitoring:*
 • `/monitor <name> <user>/<repo>`: start monitoring a repository for new commits
 • `/unmonitor <name>`: stop monitoring a repository
 • `/monitored`: list all monitored repositories in this chat
 • `/checkupdates`: force check for updates now
 
*Admin only:*
 • `/saverepo <name> <user>/<repo> <number (optional)>`: saves a repo value as shortcut
 • `/delrepo <name>`: deletes a repo shortcut
"""

__mod_name__ = "GitHub"


RELEASE_HANDLER = DisableAbleCommandHandler(
    "git", getRelease, admin_ok=True, run_async=True
)
FETCH_HANDLER = DisableAbleCommandHandler(
    "fetch", cmdFetch, admin_ok=True, run_async=True
)
SAVEREPO_HANDLER = CommandHandler("saverepo", saveRepo, run_async=True)
DELREPO_HANDLER = CommandHandler("delrepo", delRepo, run_async=True)
LISTREPO_HANDLER = DisableAbleCommandHandler(
    "listrepo", listRepo, admin_ok=True, run_async=True
)
VERCHECKER_HANDLER = DisableAbleCommandHandler(
    "gitver", getVer, admin_ok=True, run_async=True
)
CHANGELOG_HANDLER = DisableAbleCommandHandler(
    "changelog", changelog, admin_ok=True, run_async=True
)

HASHFETCH_HANDLER = RegexHandler(r"^&[^\s]+", hashFetch)

MONITOR_HANDLER = CommandHandler("monitor", add_monitor, run_async=True)
UNMONITOR_HANDLER = CommandHandler("unmonitor", remove_monitor, run_async=True)
MONITORED_HANDLER = DisableAbleCommandHandler(
    "monitored", list_monitored, admin_ok=True, run_async=True
)
CHECKUPDATES_HANDLER = DisableAbleCommandHandler(
    "checkupdates", force_check, admin_ok=True, run_async=True
)

dispatcher.add_handler(RELEASE_HANDLER)
dispatcher.add_handler(FETCH_HANDLER)
dispatcher.add_handler(SAVEREPO_HANDLER)
dispatcher.add_handler(DELREPO_HANDLER)
dispatcher.add_handler(LISTREPO_HANDLER)
dispatcher.add_handler(HASHFETCH_HANDLER)
dispatcher.add_handler(VERCHECKER_HANDLER)
dispatcher.add_handler(CHANGELOG_HANDLER)

dispatcher.add_handler(MONITOR_HANDLER)
dispatcher.add_handler(UNMONITOR_HANDLER)
dispatcher.add_handler(MONITORED_HANDLER)
dispatcher.add_handler(CHECKUPDATES_HANDLER)

start_monitor()
