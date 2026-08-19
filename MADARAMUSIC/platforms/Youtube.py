import asyncio
import os
import re
import logging
import yt_dlp
from typing import Union
from pyrogram.enums import MessageEntityType
from pyrogram.types import Message

LOGGER = logging.getLogger(__name__)

def time_to_seconds(time_str: str) -> int:
    if not time_str:
        return 0
    try:
        return sum(int(x) * 60 ** i for i, x in enumerate(reversed(str(time_str).split(":"))))
    except ValueError:
        return 0

def extract_video_id(link: str) -> str:
    if "youtu.be/" in link:
        return link.split("youtu.be/")[1].split("?")[0].split("&")[0]
    elif "v=" in link:
        return link.split("v=")[1].split("&")[0]
    return link

class YouTubeAPI:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.regex = r"(?:youtube\.com|youtu\.be)"
        self.listbase = "https://youtube.com/playlist?list="

        # Optimized options to bypass YouTube anti-bot protections natively
        self.base_opts = {
            "quiet": True,
            "no_warnings": True,
            "geo_bypass": True,
            "nocheckcertificate": True,
            # Bypasses bot detection by mimicking TV & iOS clients directly
            "extractor_args": {"youtube": ["player_client=tv_embedded,ios"]},
        }

    async def exists(self, link: str, videoid: Union[bool, str] = None) -> bool:
        if videoid:
            link = self.base + link
        return bool(re.search(self.regex, link))

    async def url(self, message_1: Message) -> Union[str, None]:
        messages = [message_1]
        if message_1.reply_to_message:
            messages.append(message_1.reply_to_message)
        for message in messages:
            if message.entities:
                for entity in message.entities:
                    if entity.type == MessageEntityType.URL:
                        text = message.text or message.caption
                        return text[entity.offset: entity.offset + entity.length]
            elif message.caption_entities:
                for entity in message.caption_entities:
                    if entity.type == MessageEntityType.TEXT_LINK:
                        return entity.url
        return None

    async def track(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        search_query = link.split("&")[0].strip()

        ydl_opts = {
            **self.base_opts,
            "skip_download": True,
            "extract_flat": True,
            "noplaylist": True,
            "default_search": "ytsearch",
        }

        lookup = search_query if re.search(self.regex, search_query) else f"ytsearch1:{search_query}"

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = await asyncio.to_thread(ydl.extract_info, lookup, False)

            entries = info.get("entries") if info else None
            res = (entries or [info])[0] if entries or info else None

            if res:
                vidid = res.get("id")
                title = res.get("title", "Unknown Title")
                dur_sec = int(res.get("duration", 0) or 0)
                m, s = divmod(dur_sec, 60)
                h, m = divmod(m, 60)
                duration_min = f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"

                return {
                    "title": title,
                    "link": f"https://www.youtube.com/watch?v={vidid}",
                    "vidid": vidid,
                    "duration_min": duration_min,
                    "thumb": f"https://img.youtube.com/vi/{vidid}/hqdefault.jpg",
                }, vidid
        except Exception as e:
            LOGGER.error(f"YouTube metadata extraction error: {e}")

        raise RuntimeError("Failed to fetch track details directly from YouTube.")

    async def details(self, link: str, videoid: Union[bool, str] = None):
        try:
            track_data, vidid = await self.track(link, videoid=videoid)
            if track_data:
                title = track_data["title"]
                duration_min = track_data["duration_min"]
                duration_sec = time_to_seconds(duration_min)
                thumb = track_data["thumb"]
                return title, duration_min, duration_sec, thumb, vidid
        except Exception:
            pass
        return None, None, None, None, None

    async def title(self, link: str, videoid: Union[bool, str] = None) -> str:
        t, _, _, _, _ = await self.details(link, videoid)
        return t or "Unknown Title"

    async def duration(self, link: str, videoid: Union[bool, str] = None) -> str:
        _, d, _, _, _ = await self.details(link, videoid)
        return d or "0:00"

    async def thumbnail(self, link: str, videoid: Union[bool, str] = None) -> str:
        vid_id_str = link if videoid else extract_video_id(link)
        if vid_id_str and len(vid_id_str) > 3:
            return f"https://img.youtube.com/vi/{vid_id_str}/hqdefault.jpg"
        return "https://telegra.ph/file/2e3d368e77c449c287430.jpg"

    async def download(
        self, link: str, mystic, video: Union[bool, str] = None, videoid: Union[bool, str] = None,
        songaudio: Union[bool, str] = None, songvideo: Union[bool, str] = None, format_id: Union[bool, str] = None,
        title: Union[bool, str] = None,
    ):
        """Extracts direct raw streaming URLs straight from YouTube without downloading files to disk."""
        if videoid:
            link = self.base + link

        fmt = "bestaudio/best" if not video else "bestvideo[height<=720]+bestaudio/best"
        ydl_opts = {
            **self.base_opts,
            "format": fmt,
            "skip_download": True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = await asyncio.to_thread(ydl.extract_info, link, False)
                stream_url = info.get("url")

                if stream_url:
                    # Returns direct direct HTTP audio/video stream URL to PyTgCalls/FFmpeg
                    return stream_url, True
        except Exception as e:
            LOGGER.error(f"Direct stream URL extraction error: {e}")

        return None, False

YouTube = YouTubeAPI()
