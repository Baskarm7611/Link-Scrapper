
import os

from helpers import *
from aiohttp import web
from dotenv import load_dotenv
from pyrogram import Client, filters, types

import contextlib

load_dotenv()
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")

ADMINS = (
    [int(i.strip()) for i in os.environ.get("ADMINS").split(",")]
    if os.environ.get("ADMINS")
    else []
)

routes = web.RouteTableDef()


@routes.get("/", allow_head=True)
async def root_route_handler(request):
    res = {
        "status": "running",
    }
    return web.json_response(res)


async def web_server():
    web_app = web.Application(client_max_size=30000000)
    web_app.add_routes(routes)
    return web_app


class Bot(Client):
    def __init__(self):
        super().__init__(
            "link-scrapper",
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=BOT_TOKEN,
        )

    async def start(self):
        await super().start()
        print("Bot started")
        app = web.AppRunner(await web_server())
        await app.setup()
        await web.TCPSite(app, "0.0.0.0", 8000).start()

    async def stop(self, *args):
        await super().stop()
        print("Bot stopped")


my_app = Bot()

@my_app.on_message(filters.command("start") & filters.user(ADMINS) & filters.private)
async def start_cmd(c, m: types.Message):
    text = "This is a bot to scrap links. Just send or forward any telegram messages or `/scrap webpage`\n\nCommands: \n/scrap\n/domain"
    return await m.reply(text)


@my_app.on_message(
    filters.command("scrap") & filters.regex(r"https?://[^\s]+") & filters.user(ADMINS)
)
async def link_scrapper_cmd(c, m: types.Message):
    url = m.matches[0].group(0)
    links = await scrap_links(url)
    filterted_links = await filter_links_by_domain(links)
    text = "".join(f"`{link}`\n" for link in filterted_links)
    chunks = [text[i:i+4000] for i in range(0, len(text), 4000)]
    for chunk in chunks:
        await m.reply(chunk, disable_web_page_preview=0)
    return


@my_app.on_message(filters.command("domain") & filters.user(ADMINS))
async def domain_cmd(c, m: types.Message):
    if len(m.command) == 1:
        return await m.reply(f"/domain example.com\n\nCurrent domain: {await get_domain_from_file()}")

    elif len(m.command) == 2:
        domain = m.command[1]
        if domain == "None":
            await write_domain_to_file("log.txt", "")
            return await m.reply("Domain removed successfully")

        await write_domain_to_file("log.txt", domain)
        return await m.reply("Domain set successfully")


@my_app.on_message(
    (filters.text | filters.caption | filters.reply_keyboard)
    & filters.private
    & filters.user(ADMINS)
)
async def link_scrapper(c, m: types.Message):
    try:
        x = m.text or m.caption
        raw_links = await extract_link(x.html) if x else ""
        links = await get_inline_keyboard_markup_url(m, raw_links)
        filterted_links = await filter_links_by_domain(links)
        text = "".join(f"`{link}`\n" for link in filterted_links)
        await m.reply(text, disable_web_page_preview=0)
    except Exception as e:
        print(e)
        await m.reply("Some error occurred. Just forward or send any message with links")


with contextlib.suppress(Exception):
    with open('log.txt', 'x') as f:
        pass  # Do nothing, just create the file.

my_app.run()
