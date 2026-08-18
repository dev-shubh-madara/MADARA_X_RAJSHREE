# -----------------------------------------------
# 🔸 RAJSHREE MUSIC BOT
# 🔹 Developed & Owned by: MADARA
# 📅 Copyright © 2025 – All Rights Reserved
#
# 📖 License: See LICENSE file
# -----------------------------------------------

import re
from os import getenv
from dotenv import load_dotenv
from pyrogram import filters

# Load environment variables
load_dotenv()

# ─── Required Credentials ───────────────────────────────────────────────────
API_ID = int(getenv("API_ID", 0))
API_HASH = getenv("API_HASH")
BOT_TOKEN = getenv("BOT_TOKEN")

if not API_ID or not API_HASH or not BOT_TOKEN:
    raise SystemExit(
        "\n[ERROR] Missing required secrets!\n"
        "Please set API_ID, API_HASH, and BOT_TOKEN in your environment variables.\n"
        "Get them from https://my.telegram.org and @BotFather on Telegram.\n"
    )

# ─── Bot & Owner Info ────────────────────────────────────────────────────────
OWNER_USERNAME  = getenv("OWNER_USERNAME", "Madara_x_coder_aura")
BOT_USERNAME    = getenv("BOT_USERNAME", "RAJSHREE_MUSIC_GMS_op_bot")
BOT_NAME        = getenv("BOT_NAME", "Rajshree")
ASSUSERNAME     = getenv("ASSUSERNAME", "RajshreeAssistant")

# ─── MongoDB ─────────────────────────────────────────────────────────────────
MONGO_DB_URI = getenv("MONGO_DB_URI", None)

# ─── Limits & IDs ────────────────────────────────────────────────────────────
DURATION_LIMIT_MIN = int(getenv("DURATION_LIMIT", 17000))
LOGGER_ID = int(getenv("LOGGER_ID", getenv("LOG_GROUP_ID", "0")))
OWNER_ID  = int(getenv("OWNER_ID", "0"))

# ─── Heroku (optional) ───────────────────────────────────────────────────────
HEROKU_APP_NAME = getenv("HEROKU_APP_NAME")
HEROKU_API_KEY  = getenv("HEROKU_API_KEY")

# ─── Git / Upstream ──────────────────────────────────────────────────────────
UPSTREAM_REPO   = getenv("UPSTREAM_REPO", "https://github.com/OnlyRoohi/Jtest")
UPSTREAM_BRANCH = getenv("UPSTREAM_BRANCH", "main")
GIT_TOKEN       = getenv("GIT_TOKEN", None)

# ─── Support Links ───────────────────────────────────────────────────────────
# Set these in your environment variables to point to your own channels/groups.
SUPPORT_CHANNEL = getenv("SUPPORT_CHANNEL", "https://t.me/rajshreemusic")
SUPPORT_CHAT    = getenv("SUPPORT_CHAT",    "https://t.me/rajshreemusichat")

# ─── Assistant Settings ──────────────────────────────────────────────────────
AUTO_LEAVING_ASSISTANT     = getenv("AUTO_LEAVING_ASSISTANT", "True")
AUTO_LEAVE_ASSISTANT_TIME  = int(getenv("ASSISTANT_LEAVE_TIME", "9000"))

# ─── Server Limits ───────────────────────────────────────────────────────────
SERVER_PLAYLIST_LIMIT         = int(getenv("SERVER_PLAYLIST_LIMIT", "3000"))
PLAYLIST_FETCH_LIMIT          = int(getenv("PLAYLIST_FETCH_LIMIT", "25"))
SONG_DOWNLOAD_DURATION        = int(getenv("SONG_DOWNLOAD_DURATION", "9999999"))
SONG_DOWNLOAD_DURATION_LIMIT  = int(getenv("SONG_DOWNLOAD_DURATION_LIMIT", "9999999"))

# ─── Spotify ─────────────────────────────────────────────────────────────────
SPOTIFY_CLIENT_ID     = getenv("SPOTIFY_CLIENT_ID", "")
SPOTIFY_CLIENT_SECRET = getenv("SPOTIFY_CLIENT_SECRET", "")

# ─── Telegram File Limits ────────────────────────────────────────────────────
TG_AUDIO_FILESIZE_LIMIT = int(getenv("TG_AUDIO_FILESIZE_LIMIT", "5242880000"))
TG_VIDEO_FILESIZE_LIMIT = int(getenv("TG_VIDEO_FILESIZE_LIMIT", "5242880000"))

# ─── Session Strings ─────────────────────────────────────────────────────────
STRING1 = getenv("STRING_SESSION",  None)
STRING2 = getenv("STRING_SESSION2", None)
STRING3 = getenv("STRING_SESSION3", None)
STRING4 = getenv("STRING_SESSION4", None)
STRING5 = getenv("STRING_SESSION5", None)
STRING6 = getenv("STRING_SESSION6", None)
STRING7 = getenv("STRING_SESSION7", None)

# ─── Miscellaneous ───────────────────────────────────────────────────────────
BANNED_USERS   = filters.user()
adminlist      = {}
lyrical        = {}
votemode       = {}
autoclean      = []
confirmer      = {}
DEBUG_IGNORE_LOG = getenv("DEBUG_IGNORE_LOG", "False").lower() == "true"

# ─── Additional IDs ──────────────────────────────────────────────────────────
LOG_GROUP_ID = int(getenv("LOG_GROUP_ID", getenv("LOGGER_ID", "0")))
SUPPORT_GROUP = getenv("SUPPORT_GROUP", SUPPORT_CHAT)

# ─── Image URLs ──────────────────────────────────────────────────────────────
_default_img = getenv("START_IMG_URL", "https://files.catbox.moe/5go4t6.jpg")
START_IMG_URLS = (
    getenv("START_IMG_URL", "https://files.catbox.moe/5go4t6.jpg").split(",")
    if "," in getenv("START_IMG_URL", "")
    else [getenv("START_IMG_URL", "https://files.catbox.moe/5go4t6.jpg")]
)

START_IMG_URL           = getenv("START_IMG_URL",    "https://files.catbox.moe/aqzdyz.jpg")
PING_IMG_URL            = getenv("PING_IMG_URL",     "https://files.catbox.moe/aqzdyz.jpg")
PLAYLIST_IMG_URL        = "https://files.catbox.moe/isffh4.jpg"
STATS_IMG_URL           = "https://files.catbox.moe/isffh4.jpg"
TELEGRAM_AUDIO_URL      = "https://files.catbox.moe/isffh4.jpg"
TELEGRAM_VIDEO_URL      = "https://files.catbox.moe/isffh4.jpg"
STREAM_IMG_URL          = "https://files.catbox.moe/isffh4.jpg"
SOUNCLOUD_IMG_URL       = "https://files.catbox.moe/ohezme.jpg"
YOUTUBE_IMG_URL         = "https://files.catbox.moe/isffh4.jpg"
SPOTIFY_ARTIST_IMG_URL  = "https://files.catbox.moe/ohezme.jpg"
SPOTIFY_ALBUM_IMG_URL   = "https://files.catbox.moe/ohezme.jpg"
SPOTIFY_PLAYLIST_IMG_URL = "https://files.catbox.moe/ohezme.jpg"

# ─── Helper ──────────────────────────────────────────────────────────────────
def time_to_seconds(time: str) -> int:
    return sum(int(x) * 60**i for i, x in enumerate(reversed(time.split(":"))))

DURATION_LIMIT = int(time_to_seconds(f"{DURATION_LIMIT_MIN}:00"))

# ─── Validate Support URLs ───────────────────────────────────────────────────
if SUPPORT_CHANNEL and not re.match(r"(?:http|https)://", SUPPORT_CHANNEL):
    raise SystemExit(
        "[ERROR] - Your SUPPORT_CHANNEL url is invalid. It must start with https://"
    )

if SUPPORT_CHAT and not re.match(r"(?:http|https)://", SUPPORT_CHAT):
    raise SystemExit(
        "[ERROR] - Your SUPPORT_CHAT url is invalid. It must start with https://"
    )
