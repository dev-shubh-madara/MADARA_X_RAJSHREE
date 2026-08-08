from pyrogram import filters
from pyrogram.enums import ButtonStyle
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from MADARAMUSIC import app
from config import BOT_USERNAME
from MADARAMUSIC.utils.errors import capture_err
import httpx

start_txt = (
    "🌟 🎶 <b>ʀᴀᴊsʜʀᴇᴇ ᴍᴜsɪᴄ</b> 🎶 🌟\n\n"
    "✨ ʙᴀᴅᴀ ᴀᴀʏᴀ ʙᴏᴛ sᴛᴀᴛs ᴅᴇᴋʜɴᴇ,\n"
    "💗 ᴘᴀʜʟᴇ ᴀᴘɴɪ ʟɪɢᴇ ᴋᴇ sᴛᴀᴛs sᴜᴅʜᴀʀ ᴊᴀᴀᴋᴇ !\n\n"
    "<pre>|| ➡️ ᴜᴩᴛɪᴍᴇ    :  𝟷ʜ:𝟹𝟺ᴍ:𝟻𝟺s\n"
    " ➡️ sᴛᴏʀᴀɢᴇ  :  𝟸𝟽.𝟺%\n"
    " ➡️ ᴄᴩᴜ      :  𝟷𝟷.𝟸%\n"
    " ➡️ ʀᴀᴍ      :  𝟷𝟽.𝟻%||</pre>\n\n"
    "🌹 ᴘᴏᴡєʀєᴅ ʙʏ» <a href=\"https://t.me/Your_fucker_dad\">𝐌ᴀᴅᴀʀᴀ ⌯</a>\n"
    "💐 🌸 🎀 ❤️"
)


@app.on_message(filters.command("repo"))
async def start(_, msg):
    buttons = [
        [
            InlineKeyboardButton(
                text="🌐 ηєᴛᴡᴏʀᴋ",
                url="https://t.me/+1NRRqUd1replNTM1",
                style=ButtonStyle.PRIMARY,
            ),
            InlineKeyboardButton(
                text="🏠 ʜᴏϻє",
                url="https://t.me/MADARA_X_SUPPORT",
                style=ButtonStyle.SUCCESS,
            ),
        ],
        [
            InlineKeyboardButton(
                text="👑 ᴍᴀsᴛᴇʀ",
                url="https://t.me/Your_fucker_dad",
                style=ButtonStyle.DANGER,
            ),
        ],
    ]

    await msg.reply_photo(
        photo="https://files.catbox.moe/pyt85v.jpg",
        caption=start_txt,
        reply_markup=InlineKeyboardMarkup(buttons),
    )
