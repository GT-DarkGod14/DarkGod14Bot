# Magisk Module- Module from AstrakoBot
# Inspired from RaphaelGang's android.py
# By DAvinash97


from datetime import datetime
import re
from urllib.parse import quote
from bs4 import BeautifulSoup
from requests import get
from telegram import Bot, Update, ParseMode, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Updater, CommandHandler, MessageHandler
from telegram.ext import CallbackContext, run_async
from ujson import loads
from yaml import load, Loader

from DarkGod14Bot import dispatcher
from DarkGod14Bot.modules.sql.clear_cmd_sql import get_clearcmd
from DarkGod14Bot.modules.github import getphh
from DarkGod14Bot.modules.helper_funcs.misc import delete

rget_headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.63 Safari/537.36"
}

def magisk(update: Update, context: CallbackContext):
    message = update.effective_message
    chat = update.effective_chat
    link = "https://raw.githubusercontent.com/topjohnwu/magisk-files/master/"
    magisk_dict = {
        "*Stable*": "stable.json",
        "\n" "*Canary*": "canary.json",
    }.items()
    msg = "*Latest Magisk Releases:*\n\n"
    for magisk_type, release_url in magisk_dict:
        data = get(link + release_url).json()
        msg += (
            f"{magisk_type}:\n"
            f'• Manager - [{data["magisk"]["version"]} ({data["magisk"]["versionCode"]})]({data["magisk"]["link"]}) \n'
        )

    delmsg = message.reply_text(
        text = msg,
        parse_mode = ParseMode.MARKDOWN,
        disable_web_page_preview = True,
    )

    cleartime = get_clearcmd(chat.id, "magisk")

    if cleartime:
        context.dispatcher.run_async(delete, delmsg, cleartime.time)

def kernelsu(update: Update, context: CallbackContext):
    message = update.effective_message
    chat = update.effective_chat
    repos = [
        ("KernelSU", "tiann/KernelSU"),
        ("KernelSU-Next", "KernelSU-Next/KernelSU-Next")
    ]

    msg = "*Latest KernelSU Releases:*\n\n"

    for repo_name, repo_path in repos:
        try:
            api_url = f"https://api.github.com/repos/{repo_path}/releases/latest"
            response = get(api_url, headers=rget_headers)
            response.raise_for_status()
            data = response.json()

            msg += f"*{repo_name}:*\n"
            msg += f'• Release - [{data["tag_name"]}]({data["html_url"]})\n'

            apk_assets = [asset for asset in data["assets"] if asset["name"].lower().endswith(".apk")]
            if apk_assets:
                for asset in apk_assets:
                    msg += f'• APK - [{asset["name"]}]({asset["browser_download_url"]})\n'
            else:
                msg += "• APK - No APK assets found\n"

            msg += "\n"

        except Exception as e:
            msg += f"*{repo_name}:* Error fetching data ({str(e)})\n\n"
            continue

    if "Error fetching data" in msg:
        msg += "\n⚠️ Failed to fetch some releases, try again later."

    delmsg = message.reply_text(
        text=msg,
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=True,
    )

    cleartime = get_clearcmd(chat.id, "kernelsu")

    if cleartime:
        context.dispatcher.run_async(delete, delmsg, cleartime.time)

def checkfw(update: Update, context: CallbackContext):
    args = context.args
    message = update.effective_message
    chat = update.effective_chat
    
    if len(args) == 2:
        temp, csc = args
        model = f'sm-' + temp if not temp.upper().startswith('SM-') else temp
        fota = get(
            f'https://fota-cloud-dn.ospserver.net/firmware/{csc.upper()}/{model.upper()}/version.xml',
            headers=rget_headers
        )

        if fota.status_code != 200:
            msg = f"Couldn't check for {temp.upper()} and {csc.upper()}, please refine your search or try again later!"

        else:
            page = BeautifulSoup(fota.content, 'xml')
            os = page.find("latest").get("o")

            if page.find("latest").text.strip():
                msg = f'*Latest released firmware for {model.upper()} and {csc.upper()} is:*\n'
                pda, csc, phone = page.find("latest").text.strip().split('/')
                msg += f'• PDA: `{pda}`\n• CSC: `{csc}`\n'
                if phone:
                    msg += f'• Phone: `{phone}`\n'
                if os:
                    msg += f'• Android: `{os}`\n'
                msg += ''
            else:
                msg = f'*No public release found for {model.upper()} and {csc.upper()}.*\n\n'

    else:
        msg = 'Give me something to fetch, like:\n`/checkfw SM-N975F DBT`'

    delmsg = message.reply_text(
        text = msg,
        parse_mode = ParseMode.MARKDOWN,
        disable_web_page_preview = True,
    )

    cleartime = get_clearcmd(chat.id, "checkfw")

    if cleartime:
        context.dispatcher.run_async(delete, delmsg, cleartime.time)


def getfw(update: Update, context: CallbackContext):
    args = context.args
    message = update.effective_message
    chat = update.effective_chat
    btn = ""
    
    if len(args) == 2:
        temp, csc = args
        model = f'sm-' + temp if not temp.upper().startswith('SM-') else temp
        fota = get(
            f'https://fota-cloud-dn.ospserver.net/firmware/{csc.upper()}/{model.upper()}/version.xml',
            headers=rget_headers
        )

        if fota.status_code != 200:
            msg = f"Couldn't check for {temp.upper()} and {csc.upper()}, please refine your search or try again later!"

        else:
            url1 = f'https://samfrew.com/model/{model.upper()}/region/{csc.upper()}/'
            url2 = f'https://www.sammobile.com/samsung/firmware/{model.upper()}/{csc.upper()}/'
            url3 = f'https://sfirmware.com/samsung-{model.lower()}/#tab=firmwares'
            url4 = f'https://samfw.com/firmware/{model.upper()}/{csc.upper()}/'
            page = BeautifulSoup(fota.content, 'xml')
            os = page.find("latest").get("o")
            msg = ""
            if page.find("latest").text.strip():
                pda, csc2, phone = page.find("latest").text.strip().split('/')
                msg += f'*Latest firmware for {model.upper()} and {csc.upper()} is:*\n'
                msg += f'• PDA: `{pda}`\n• CSC: `{csc2}`\n'
                if phone:
                    msg += f'• Phone: `{phone}`\n'
                if os:
                    msg += f'• Android: `{os}`\n'
            msg += '\n'
            msg += f'*Downloads for {model.upper()} and {csc.upper()}*\n'
            btn = [[InlineKeyboardButton(text=f"Samfrew", url = url1)]]
            btn += [[InlineKeyboardButton(text=f"Sammobile", url = url2)]]
            btn += [[InlineKeyboardButton(text=f"SFirmware", url = url3)]]
            btn += [[InlineKeyboardButton(text=f"Samfw (Recommended)", url = url4)]]
    else:
        msg = 'Give me something to fetch, like:\n`/getfw SM-N975F DBT`'

    delmsg = message.reply_text(
        text = msg,
        reply_markup = InlineKeyboardMarkup(btn),
        parse_mode = ParseMode.MARKDOWN,
        disable_web_page_preview = True,
    )

    cleartime = get_clearcmd(chat.id, "getfw")

    if cleartime:
        context.dispatcher.run_async(delete, delmsg, cleartime.time)


def phh(update: Update, context: CallbackContext):
    args = context.args
    message = update.effective_message
    chat = update.effective_chat
    index = int(args[0]) if len(args) > 0 and args[0].isdigit() else 0
    text = getphh(index)

    delmsg = message.reply_text(
        text,
        parse_mode = ParseMode.HTML,
        disable_web_page_preview = True,
    )

    cleartime = get_clearcmd(chat.id, "phh")

    if cleartime:
        context.dispatcher.run_async(delete, delmsg, cleartime.time)


def miui(update: Update, context: CallbackContext):
    message = update.effective_message
    chat = update.effective_chat
    device = message.text[len("/miui ") :]
    markup = []

    if device:
        link = "https://raw.githubusercontent.com/XiaomiFirmwareUpdater/miui-updates-tracker/master/data/latest.yml"
        yaml_data = load(get(link).content, Loader=Loader)
        data = [i for i in yaml_data if device in i['codename']]

        if not data:
            msg = f"Miui is not avaliable for {device}"
        else:
            for fw in data:
                av = fw['android']
                branch = fw['branch']
                method = fw['method']
                link = fw['link']
                fname = fw['name']
                version = fw['version']
                size = fw['size']
                btn = fname + ' | ' + branch + ' | ' + method + ' | ' + version + ' | ' + av + ' | ' + size
                markup.append([InlineKeyboardButton(text = btn, url = link)])

            device = fname.split(" ")
            device.pop()
            device = " ".join(device)
            msg = f"The latest firmwares for the *{device}* are:"
    else:
        msg = 'Give me something to fetch, like:\n`/miui whyred`'

    delmsg = message.reply_text(
        text = msg,
        reply_markup = InlineKeyboardMarkup(markup),
        parse_mode = ParseMode.MARKDOWN,
        disable_web_page_preview = True,
    )

    cleartime = get_clearcmd(chat.id, "miui")

    if cleartime:
        context.dispatcher.run_async(delete, delmsg, cleartime.time)


def orangefox(update: Update, context: CallbackContext):
    message = update.effective_message
    chat = update.effective_chat
    args = context.args
    
    # Obtener el dispositivo desde argumentos o desde el texto del mensaje
    if args:
        device = args[0]
    else:
        # Detectar qué comando se usó para extraer correctamente el dispositivo
        text = message.text.strip()
        if text.startswith("/orangefox "):
            device = text[len("/orangefox ") :].strip()
        elif text.startswith("/ofox "):
            device = text[len("/ofox ") :].strip()
        else:
            device = ""
    
    btn = ""

    if device:
        link = get(f"https://api.orangefox.download/v3/releases/?codename={device}&sort=date_desc&limit=1")

        page = loads(link.content)
        file_id = page["data"][0]["_id"] if "data" in page else ""
        link = get(f"https://api.orangefox.download/v3/devices/get?codename={device}")
        page = loads(link.content)
        if "detail" in page and page["detail"] == "Not Found":
            msg = f"OrangeFox recovery is not avaliable for {device}"
        else:
            oem = page["oem_name"]
            model = page["model_name"]
            full_name = page["full_name"]
            maintainer = page["maintainer"]["username"]
            link = get(f"https://api.orangefox.download/v3/releases/get?_id={file_id}")
            page = loads(link.content)
            dl_file = page["filename"]
            build_type = page["type"]
            version = page["version"]
            changelog = page["changelog"][0]
            size = str(round(float(page["size"]) / 1024 / 1024, 1)) + "MB"
            dl_link = page["mirrors"][next(iter(page["mirrors"]))]
            date = datetime.fromtimestamp(page["date"])
            md5 = page["md5"]
            msg = f"*Latest OrangeFox Recovery for the {full_name}*\n\n"
            msg += f"• Manufacturer: `{oem}`\n"
            msg += f"• Model: `{model}`\n"
            msg += f"• Codename: `{device}`\n"
            msg += f"• Build type: `{build_type}`\n"
            msg += f"• Maintainer: `{maintainer}`\n"
            msg += f"• Version: `{version}`\n"
            msg += f"• Changelog: `{changelog}`\n"
            msg += f"• Size: `{size}`\n"
            msg += f"• Date: `{date}`\n"
            msg += f"• File: `{dl_file}`\n"
            msg += f"• MD5: `{md5}`\n"
            btn = [[InlineKeyboardButton(text=f"Download", url = dl_link)]]
    else:
        msg = 'Give me something to fetch, like:\n`/orangefox a3y17lte` or `/ofox a3y17lte`'

    delmsg = message.reply_text(
        text = msg,
        reply_markup = InlineKeyboardMarkup(btn),
        parse_mode = ParseMode.MARKDOWN,
        disable_web_page_preview = True,
    )

    cleartime = get_clearcmd(chat.id, "orangefox")

    if cleartime:
        context.dispatcher.run_async(delete, delmsg, cleartime.time)


def twrp(update: Update, context: CallbackContext):
    message = update.effective_message
    chat = update.effective_chat
    device = message.text[len("/twrp ") :]
    btn = ""

    if device:
        link = get(f"https://eu.dl.twrp.me/{device}")

        if link.status_code == 404:
            msg = f"TWRP is not avaliable for {device}"
        else:
            page = BeautifulSoup(link.content, "lxml")
            download = page.find("table").find("tr").find("a")
            dl_link = f"https://eu.dl.twrp.me{download['href']}"
            dl_file = download.text
            size = page.find("span", {"class": "filesize"}).text
            date = page.find("em").text.strip()
            msg = f"*Latest TWRP for the {device}*\n\n"
            msg += f"• Size: `{size}`\n"
            msg += f"• Date: `{date}`\n"
            msg += f"• File: `{dl_file}`\n\n"
            btn = [[InlineKeyboardButton(text=f"Download", url = dl_link)]]
    else:
        msg = 'Give me something to fetch, like:\n`/twrp a3y17lte`'

    delmsg = message.reply_text(
        text = msg,
        reply_markup = InlineKeyboardMarkup(btn),
        parse_mode = ParseMode.MARKDOWN,
        disable_web_page_preview = True,
    )

    cleartime = get_clearcmd(chat.id, "twrp")

    if cleartime:
        context.dispatcher.run_async(delete, delmsg, cleartime.time)


def specs(update: Update, context: CallbackContext):
    message = update.effective_message
    chat = update.effective_chat
    args = context.args
    if args:
        device_query = " ".join(args)
    else:
        device_query = message.text[len("/specs "):].strip()
    if not device_query:
        msg = 'Give me something to search, like:\n`/specs iPhone 15 Pro`\nor\n`/specs Samsung Galaxy S24`'
        delmsg = message.reply_text(text=msg, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)
        cleartime = get_clearcmd(chat.id, "specs")
        if cleartime:
            context.dispatcher.run_async(delete, delmsg, cleartime.time)
        return
    search_msg = message.reply_text(f"🔍 Searching specifications for {device_query}...")
    try:
        search_url = f"https://www.gsmarena.com/results.php3?sQuickSearch=yes&sName={quote(device_query)}"
        response = get(search_url, headers=rget_headers, timeout=10)
        if response.status_code != 200:
            msg = f"⚠️ Error searching for {device_query}"
            search_msg.edit_text(msg)
            return
        soup = BeautifulSoup(response.content, 'html.parser')
        device_links = []
        makers_div = soup.find('div', class_='makers')
        if makers_div:
            links = makers_div.find_all('a', href=True)
            for link in links:
                href = link.get('href')
                if href and href.endswith('.php'):
                    device_links.append(f"https://www.gsmarena.com/{href}")
        if not device_links:
            msg = f"⚠️ No results found for {device_query}"
            search_msg.edit_text(msg)
            return
        phone_url = None
        device_query_lower = device_query.lower().replace(' ', '')
        for link in device_links:
            link_name = link.split('/')[-1].replace('.php', '').replace('_', ' ').replace('-', ' ')
            link_name_clean = link_name.lower().replace(' ', '')
            if link_name_clean == device_query_lower:
                phone_url = link
                break
        if not phone_url:
            best_match = None
            best_score = 0
            for link in device_links:
                link_name = link.split('/')[-1].replace('.php', '').replace('_', ' ').replace('-', ' ')
                link_name_clean = link_name.lower().replace(' ', '')
                score = 0
                query_words = device_query.lower().split()
                link_words = link_name.lower().split()
                matching_words = sum(1 for word in query_words if word in link_words)
                score = matching_words / len(query_words) if query_words else 0
                if device_query_lower in link_name_clean:
                    score += 0.5
                extra_words = len(link_words) - len(query_words)
                if extra_words > 0:
                    score -= (extra_words * 0.1)
                if score > best_score:
                    best_score = score
                    best_match = link
            phone_url = best_match if best_match else device_links[0]
        phone_response = get(phone_url, headers=rget_headers, timeout=10)
        if phone_response.status_code != 200:
            msg = "⚠️ Error loading device page"
            search_msg.edit_text(msg)
            return
        phone_soup = BeautifulSoup(phone_response.content, 'html.parser')
        phone_name = None
        name_elem = phone_soup.find('h1', class_='specs-phone-name-title')
        if name_elem:
            phone_name = name_elem.get_text().strip()
        if not phone_name:
            phone_name = device_query.title()
        all_specs = {}
        specs_div = phone_soup.find('div', {'id': 'specs-list'})
        if specs_div:
            tables = specs_div.find_all('table', {'cellspacing': '0'})
            for table in tables:
                current_category = None
                rows = table.find_all('tr')
                for row in rows:
                    th = row.find('th', {'scope': 'row'})
                    if th:
                        current_category = th.get_text().strip()
                        if current_category not in all_specs:
                            all_specs[current_category] = {}
                    ttl_cell = row.find('td', {'class': 'ttl'})
                    nfo_cell = row.find('td', {'class': 'nfo'})
                    if ttl_cell and nfo_cell:
                        spec_name_elem = ttl_cell.find('a')
                        if spec_name_elem:
                            spec_name = spec_name_elem.get_text().strip()
                        else:
                            spec_name = ttl_cell.get_text().strip()
                        spec_value = nfo_cell.get_text().strip()
                        spec_value = re.sub(r'\s+', ' ', spec_value).strip()
                        if spec_name and spec_value and spec_value != '-' and current_category:
                            if len(spec_value) > 200:
                                spec_value = spec_value[:200] + "..."
                            all_specs[current_category][spec_name] = spec_value
        if all_specs:
            msg = f"*📱 {phone_name}*\n\n"
            important_order = ['Network', 'Launch', 'Body', 'Display', 'Platform', 'Memory', 'Main Camera', 'Selfie Camera', 'Battery']
            shown_categories = []
            for category in important_order:
                for cat_name, specs in all_specs.items():
                    if category.lower() in cat_name.lower() and specs:
                        msg += f"*{cat_name.upper()}*\n"
                        count = 0
                        for spec_name, spec_value in specs.items():
                            if count < 5:
                                if len(spec_value) > 100:
                                    spec_value = spec_value[:100] + "..."
                                msg += f"• *{spec_name}*: `{spec_value}`\n"
                                count += 1
                        msg += "\n"
                        shown_categories.append(cat_name)
                        break
            for cat_name, specs in all_specs.items():
                if cat_name not in shown_categories and len(msg) < 3500:
                    if specs:
                        msg += f"*{cat_name.upper()}*\n"
                        count = 0
                        for spec_name, spec_value in specs.items():
                            if count < 3:
                                if len(spec_value) > 100:
                                    spec_value = spec_value[:100] + "..."
                                msg += f"• *{spec_name}*: `{spec_value}`\n"
                                count += 1
                        msg += "\n"
            if len(msg) > 4000:
                msg = msg[:3900] + "\n\n`...truncated`"
        else:
            msg = f"*📱 {phone_name}*\n\n`⚠️ Could not extract specifications`\n`Try checking manually:` {phone_url}"
    except Exception as e:
        msg = f"⚠️ Error processing {device_query}: `{str(e)}`"
    search_msg.delete()
    delmsg = message.reply_text(text=msg, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)
    cleartime = get_clearcmd(chat.id, "specs")
    if cleartime:
        context.dispatcher.run_async(delete, delmsg, cleartime.time)



__help__ = """
*Available commands:*\n
*Magisk:* 
• `/magisk`, `/su`, `/root`: fetches latest magisk\n
*KernelSU:*
• `/kernelsu`: fetches latest kernelsu\n
*OrangeFox Recovery Project:* 
• `/orangefox` or `/ofox` `<devicecodename>`: fetches lastest OrangeFox Recovery available for a given device codename\n
*TWRP:* 
• `/twrp <devicecodename>`: fetches lastest TWRP available for a given device codename\n
*MIUI:*
• `/miui <devicecodename>`- fetches latest firmware info for a given device codename\n
*Phh:* 
• `/phh`: get lastest phh builds from github\n
*Samsung:*
• `/checkfw <model> <csc>` - Samsung only - shows the latest firmware info for the given device, taken from samsung servers
• `/getfw <model> <csc>` - Samsung only - gets firmware download links from samfrew, sammobile and sfirmwares for the given device\n
*Specs:*
• `/specs <device name>`: get phone specs and info
"""

MAGISK_HANDLER = CommandHandler(["magisk", "root", "su"], magisk, run_async=True)
KERNELSU_HANDLER = CommandHandler("kernelsu", kernelsu, run_async=True)
ORANGEFOX_HANDLER = CommandHandler(["orangefox", "ofox"], orangefox, run_async=True)
TWRP_HANDLER = CommandHandler("twrp", twrp, run_async=True)
GETFW_HANDLER = CommandHandler("getfw", getfw, run_async=True)
CHECKFW_HANDLER = CommandHandler("checkfw", checkfw, run_async=True)
PHH_HANDLER = CommandHandler("phh", phh, run_async=True)
MIUI_HANDLER = CommandHandler("miui", miui, run_async=True)
SPECS_HANDLER = CommandHandler("specs", specs, run_async=True)

dispatcher.add_handler(MAGISK_HANDLER)
dispatcher.add_handler(KERNELSU_HANDLER)
dispatcher.add_handler(ORANGEFOX_HANDLER)
dispatcher.add_handler(TWRP_HANDLER)
dispatcher.add_handler(GETFW_HANDLER)
dispatcher.add_handler(CHECKFW_HANDLER)
dispatcher.add_handler(PHH_HANDLER)
dispatcher.add_handler(MIUI_HANDLER)
dispatcher.add_handler(SPECS_HANDLER)

__mod_name__ = "Android"
__command_list__ = ["magisk", "kernelsu", "root", "su", "orangefox", "ofox", "twrp", "checkfw", "getfw", "phh", "miui", "specs"]
__handlers__ = [MAGISK_HANDLER, KERNELSU_HANDLER, ORANGEFOX_HANDLER, TWRP_HANDLER, GETFW_HANDLER, CHECKFW_HANDLER, PHH_HANDLER, MIUI_HANDLER, SPECS_HANDLER]
