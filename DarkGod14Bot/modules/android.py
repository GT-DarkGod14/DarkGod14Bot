# Magisk Module- Module from AstrakoBot
# Inspired from RaphaelGang's android.py
# By DAvinash97


from datetime import datetime
import re
from urllib.parse import quote, urlparse
from bs4 import BeautifulSoup
from requests import get, Session, RequestException
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


GSM_SEARCH_HOSTS = ("https://m.gsmarena.com", "https://www.gsmarena.com")
GSM_PAGE_HOSTS = ("https://www.gsmarena.com", "https://m.gsmarena.com")

gsm_headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

_GSM_PHONE_SLUG = re.compile(r"^[^/]+-\d+\.php$")
_GSM_NOT_PHONE = re.compile(
    r"-(?:phones|reviews?|pictures|news|videos|related|compare|opinions)-", re.I
)


class GSMArenaBlocked(Exception):
    pass


def _gsm_is_blocked(response):
    if response.status_code in (403, 429, 503):
        return True
    head = response.text[:4000].lower()
    return "turnstile" in head or "one quick check before you continue" in head


def _gsm_get(session, path, hosts, params=None):
    blocked = False
    last_error = None
    for host in hosts:
        try:
            resp = session.get(
                host + path, params=params, headers=gsm_headers, timeout=15
            )
        except RequestException as e:
            last_error = e
            continue
        if _gsm_is_blocked(resp):
            blocked = True
            continue
        if resp.status_code == 200:
            return resp
        last_error = RuntimeError(f"HTTP {resp.status_code} from {host}")
    if blocked:
        raise GSMArenaBlocked()
    raise last_error or RuntimeError("GSMArena request failed")


def _gsm_norm(text):
    return re.sub(r"[^a-z0-9]+", "", text.lower())


def _gsm_tokens(text):
    return re.findall(r"[a-z0-9]+", text.lower())


def _gsm_extract_candidates(soup):
    containers = [
        soup.select_one("div.makers"),
        soup.select_one("div#review-body"),
        soup.select_one("div.section-body"),
        soup,
    ]
    for container in containers:
        if container is None:
            continue
        found, seen = [], set()
        for a in container.find_all("a", href=True):
            slug = urlparse(a["href"]).path.rsplit("/", 1)[-1]
            if not _GSM_PHONE_SLUG.match(slug) or _GSM_NOT_PHONE.search(slug):
                continue
            if slug in seen:
                continue
            seen.add(slug)
            name = a.get_text(" ", strip=True)
            if not name and a.find("img"):
                name = (a.find("img").get("title") or a.find("img").get("alt") or "").strip()
            if not name:
                name = re.sub(r"-\d+\.php$", "", slug).replace("_", " ")
            found.append((name, slug))
        if found:
            return found
    return []


def _gsm_pick_best(query, candidates):
    q_norm = _gsm_norm(query)
    q_tokens = _gsm_tokens(query)
    if not q_tokens:
        return None
    best, best_score = None, 0.0
    for idx, (name, slug) in enumerate(candidates):
        n_norm = _gsm_norm(name)
        n_tokens = set(_gsm_tokens(name))
        ratio = sum(1 for t in q_tokens if t in n_tokens) / len(q_tokens)
        if ratio < 0.5:
            continue
        score = ratio
        if n_norm == q_norm:
            score += 2
        elif n_norm.endswith(q_norm):
            score += 1.5
        elif q_norm in n_norm:
            score += 0.5
        extra = len(n_tokens) - len(q_tokens)
        if extra > 0:
            score -= 0.05 * extra
        score -= idx * 0.001
        if score > best_score:
            best, best_score = (name, slug), score
    return best


def _gsm_parse_specs(soup):
    all_specs = {}
    for table in soup.find_all("table"):
        current = None
        last_name = None
        for row in table.find_all("tr"):
            th = row.find("th")
            if th:
                current = th.get_text(" ", strip=True)
                all_specs.setdefault(current, {})
                last_name = None
            ttl = row.find("td", class_="ttl")
            nfo = row.find("td", class_="nfo")
            if not (ttl and nfo and current):
                continue
            name = ttl.get_text(" ", strip=True)
            value = re.sub(r"\s+", " ", nfo.get_text(" ", strip=True)).strip()
            if not value or value == "-":
                continue
            if name:
                all_specs[current][name] = value
                last_name = name
            elif last_name:
                all_specs[current][last_name] += "; " + value
    return {k: v for k, v in all_specs.items() if v}


def _gsm_md(text):
    return re.sub(r"([_*`\[])", r"\\\1", text)


def _gsm_format(phone_name, all_specs, phone_url):
    msg = f"*📱 {_gsm_md(phone_name)}*\n\n"
    important_order = [
        "Network", "Launch", "Body", "Display", "Platform",
        "Memory", "Main Camera", "Selfie Camera", "Battery",
    ]

    def block(cat_name, specs_dict, limit):
        out = f"*{_gsm_md(cat_name.upper())}*\n"
        for spec_name, spec_value in list(specs_dict.items())[:limit]:
            spec_value = spec_value.replace("`", "'")
            if len(spec_value) > 100:
                spec_value = spec_value[:100] + "..."
            out += f"• *{_gsm_md(spec_name)}*: `{spec_value}`\n"
        return out + "\n"

    shown = set()
    for wanted in important_order:
        for cat_name, specs_dict in all_specs.items():
            if cat_name not in shown and wanted.lower() in cat_name.lower():
                msg += block(cat_name, specs_dict, 5)
                shown.add(cat_name)
                break
    for cat_name, specs_dict in all_specs.items():
        if cat_name not in shown and len(msg) < 3500:
            msg += block(cat_name, specs_dict, 3)

    msg += f"[Full specs on GSMArena]({phone_url})"
    if len(msg) > 4000:
        msg = msg[:3900] + f"\n\n`...truncated`\n[Full specs on GSMArena]({phone_url})"
    return msg


def specs(update: Update, context: CallbackContext):
    message = update.effective_message
    chat = update.effective_chat
    args = context.args
    if args:
        device_query = " ".join(args)
    else:
        device_query = message.text[len("/specs "):].strip()

    def finish(text, delete_search=True):
        if delete_search:
            try:
                search_msg.delete()
            except Exception:
                pass
        delmsg = message.reply_text(
            text=text, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True
        )
        cleartime = get_clearcmd(chat.id, "specs")
        if cleartime:
            context.dispatcher.run_async(delete, delmsg, cleartime.time)

    if not device_query:
        search_msg = None
        finish(
            'Give me something to search, like:\n`/specs iPhone 15 Pro`\nor\n`/specs Samsung Galaxy S24`',
            delete_search=False,
        )
        return

    search_msg = message.reply_text(f"🔍 Searching specifications for {device_query}...")
    manual_url = f"https://www.gsmarena.com/results.php3?sQuickSearch=yes&sName={quote(device_query)}"

    try:
        session = Session()

        resp = _gsm_get(
            session, "/results.php3", GSM_SEARCH_HOSTS,
            params={"sQuickSearch": "yes", "sName": device_query},
        )
        candidates = _gsm_extract_candidates(BeautifulSoup(resp.content, "html.parser"))
        best = _gsm_pick_best(device_query, candidates)
        if not best:
            finish(f"⚠️ No results found for {_gsm_md(device_query)}")
            return
        phone_name, slug = best

        phone_resp = _gsm_get(session, "/" + slug, GSM_PAGE_HOSTS)
        phone_soup = BeautifulSoup(phone_resp.content, "html.parser")
        phone_url = f"https://www.gsmarena.com/{slug}"

        name_elem = phone_soup.find("h1", class_="specs-phone-name-title") or phone_soup.find("h1")
        if name_elem and name_elem.get_text(strip=True):
            phone_name = name_elem.get_text(" ", strip=True)

        all_specs = _gsm_parse_specs(phone_soup)
        if all_specs:
            msg = _gsm_format(phone_name, all_specs, phone_url)
        else:
            msg = (
                f"*📱 {_gsm_md(phone_name)}*\n\n`⚠️ Could not extract specifications`\n"
                f"Try checking manually: {phone_url}"
            )
    except GSMArenaBlocked:
        msg = (
            "⚠️ GSMArena is blocking automated requests right now (anti-bot check).\n"
            f"Try again in a few minutes or search manually: {manual_url}"
        )
    except Exception as e:
        msg = f"⚠️ Error processing {_gsm_md(device_query)}: `{str(e)}`"

    finish(msg)



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
