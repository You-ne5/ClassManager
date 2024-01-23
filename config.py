from dotenv import load_dotenv

load_dotenv()

from os import environ as env

#discord
DISCORD_TOKEN = env["TOKEN"]
DLG_ID : int = int(env["DLG_ID"])
ANNOUNCE_CHANNEL_ID : int = int(env["ANNOUNCE_CHANNEL_ID"])
ADMIN_ROLE_ID : int = int(env["ADMIN_ROLE_ID"])
HELP_CATEGORY_ID : int = int(env["HELP_CATEGORY_ID"])
LESSONS_CATEGORY_ID : int = int(env["LESSONS_CATEGORY_ID"])
HELP_ARCHIVE_CATEGORY_ID : int = int(env["HELP_ARCHIVE_CATEGORY_ID"])

#code
EMBED_COLOR = 0Xd4af37