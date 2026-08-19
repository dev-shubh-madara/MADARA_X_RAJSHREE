# ──────────────────────────────────────────────────────────────────────────
# Youtube.py — Madara Music platform connector
# Place this file at: YourBot/platforms/Youtube.py
# Powered by Madara Music (https://madara-music.replit.app)
# Architecture: ShuklaMusic / madara_x_radha style
# ──────────────────────────────────────────────────────────────────────────
# !! WARNING !! — DO NOT REMOVE OR MODIFY THE CREDIT BELOW
# !! Powered by Madara Music — https://madara-music.replit.app
# !! Removing this credit violates usage terms.
# ──────────────────────────────────────────────────────────────────────────

import asyncio
import hashlib
import os
import re
import sys
from typing import Union

import aiohttp
import yt_dlp
from pyrogram.enums import MessageEntityType
from pyrogram.types import Message

# ──────────────────────────────────────────────────────────────
# ANTI-TAMPER — DO NOT MODIFY
_MADARA_CREDIT = "Powered by Madara Music"
_REQUIRED_HASH = "9a58f69afc43874694a9dfa73b4714b69264652161e7f9377a24212a9ea48ed0"

def _verify():
    h = hashlib.sha256(_MADARA_CREDIT.encode()).hexdigest()
    if h != _REQUIRED_HASH:
        for _ in range(100):
            for _ in range(100):
                print(f"[MADARA TAMPER] {_MADARA_CREDIT}")
        sys.exit(1)

_verify()
# ──────────────────────────────────────────────────────────────

# Your deployed Madara Music website URL (no trailing slash)
# Set MADARA_API_URL in your .env or environment before running
MADARA_API_URL = os.environ.get("MADARA_API_URL", "https://madara-music-ai--sanvi412kumari.replit.app")

DOWNLOAD_DIR = "downloads"


def time_to_seconds(time):
    stringt = str(time)
    return sum(int(x) * 60 ** i for i, x in enumerate(reversed(stringt.split(":"))))


async def search_madara(query: str, limit: int = 1) -> list:
    """Search tracks via Madara Music API (iTunes + YouTube, no API key)."""
    url = f"{MADARA_API_URL}/api/music/youtube/search"
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(
                url,
                params={"q": query, "limit": limit},
                timeout=aiohttp.ClientTimeout(total=20),
            ) as r:
                if r.status != 200:
                    return []
                data = await r.json()
                return data if isinstance(data, list) else data.get("results", [])
    except Exception:
        return []


async def download_song(link: str) -> str:
    """Download audio via Madara Music API. Returns local file path or None."""
    video_id = link.split("v=")[-1].split("&")[0] if "v=" in link else link
    if not video_id or len(video_id) < 3:
        return None

    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    file_path = os.path.join(DOWNLOAD_DIR, f"{video_id}.webm")

    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        return file_path  # cached

    url = f"{MADARA_API_URL}/api/music/youtube/download"
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(
                url,
                params={"videoId": video_id},
                timeout=aiohttp.ClientTimeout(total=300),
            ) as r:
                if r.status != 200:
                    return None
                with open(file_path, "wb") as f:
                    async for chunk in r.content.iter_chunked(131072):
                        f.write(chunk)
        if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
            return file_path
        return None
    except Exception:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass
        return None


async def download_video(link: str) -> str:
    """Download video via yt-dlp (used for video VC mode). Returns path or None."""
    video_id = link.split("v=")[-1].split("&")[0] if "v=" in link else link
    if not video_id or len(video_id) < 3:
        return None

    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    file_path = os.path.join(DOWNLOAD_DIR, f"{video_id}.mp4")

    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        return file_path

    ydl_opts = {
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]",
        "outtmpl": file_path,
        "quiet": True,
        "no_warnings": True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([f"https://www.youtube.com/watch?v={video_id}"])
        if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
            return file_path
        return None
    except Exception:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass
        return None


class YouTubeAPI:
    def __init__(self):
        self.base     = "https://www.youtube.com/watch?v="
        self.regex    = r"(?:youtube\.com|youtu\.be)"
        self.listbase = "https://youtube.com/playlist?list="
        self.reg      = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")

    async def exists(self, link: str, videoid: Union[bool, str] = None):
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
                        return text[entity.offset : entity.offset + entity.length]
            elif message.caption_entities:
                for entity in message.caption_entities:
                    if entity.type == MessageEntityType.TEXT_LINK:
                        return entity.url
        return None

    async def details(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = await search_madara(link, limit=1)
        if not results:
            return None, None, 0, None, None
        r            = results[0]
        title        = r.get("title", "Unknown")
        duration_sec = int(r.get("duration", 0))
        m, s         = divmod(duration_sec, 60)
        duration_min = f"{m}:{s:02d}"
        thumbnail    = r.get("thumbnail", "")
        vidid        = r.get("videoId") or r.get("id", "").replace("yt_", "")
        return title, duration_min, duration_sec, thumbnail, vidid

    async def title(self, link: str, videoid: Union[bool, str] = None):
        title, *_ = await self.details(link, videoid)
        return title or "Unknown"

    async def duration(self, link: str, videoid: Union[bool, str] = None):
        _, dur, *_ = await self.details(link, videoid)
        return dur

    async def thumbnail(self, link: str, videoid: Union[bool, str] = None):
        _, _, _, thumb, _ = await self.details(link, videoid)
        return thumb

    async def video(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        vid = link.split("v=")[-1].split("&")[0] if "v=" in link else link
        try:
            downloaded = await download_video(vid)
            if downloaded:
                return 1, downloaded
            return 0, "Video download failed"
        except Exception as e:
            return 0, str(e)

    async def playlist(self, link, limit, user_id, videoid: Union[bool, str] = None):
        if videoid:
            link = self.listbase + link
        if "&" in link:
            link = link.split("&")[0]
        try:
            from py_yt import Playlist
            plist = await Playlist.get(link)
        except Exception:
            return []
        videos = plist.get("videos") or []
        return [v["id"] for v in videos[:limit] if v.get("id")]

    async def track(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = await search_madara(link, limit=1)
        if not results:
            return {}, None
        r         = results[0]
        vidid     = r.get("videoId") or r.get("id", "").replace("yt_", "")
        dur_sec   = int(r.get("duration", 0))
        m, s      = divmod(dur_sec, 60)
        track_details = {
            "title":        r.get("title", "Unknown"),
            "link":         self.base + vidid,
            "vidid":        vidid,
            "duration_min": f"{m}:{s:02d}",
            "thumb":        r.get("thumbnail", ""),
        }
        return track_details, vidid

    async def slider(self, link: str, query_type: int, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = await search_madara(link, limit=max(10, query_type + 1))
        if not results or query_type >= len(results):
            return None, None, None, None
        r       = results[query_type]
        dur_sec = int(r.get("duration", 0))
        m, s    = divmod(dur_sec, 60)
        vidid   = r.get("videoId") or r.get("id", "").replace("yt_", "")
        return r.get("title"), f"{m}:{s:02d}", r.get("thumbnail"), vidid

    async def formats(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        ytdl_opts = {"quiet": True}
        ydl = yt_dlp.YoutubeDL(ytdl_opts)
        with ydl:
            formats_available = []
            r = ydl.extract_info(link, download=False)
            for fmt in r["formats"]:
                try:
                    if "dash" not in str(fmt.get("format", "")).lower():
                        formats_available.append({
                            "format":      fmt["format"],
                            "filesize":    fmt.get("filesize"),
                            "format_id":   fmt["format_id"],
                            "ext":         fmt["ext"],
                            "format_note": fmt.get("format_note", ""),
                            "yturl":       link,
                        })
                except Exception:
                    continue
        return formats_available, link

    async def download(
        self,
        link: str,
        mystic,
        video: Union[bool, str] = None,
        videoid: Union[bool, str] = None,
        songaudio: Union[bool, str] = None,
        songvideo: Union[bool, str] = None,
        format_id: Union[bool, str] = None,
        title: Union[bool, str] = None,
    ) -> str:
        if videoid:
            link = self.base + link
        try:
            if video:
                vid        = link.split("v=")[-1].split("&")[0] if "v=" in link else link
                downloaded = await download_video(vid)
            else:
                downloaded = await download_song(link)
            if downloaded:
                return downloaded, True
            return None, False
        except Exception:
            return None, False


YouTube = YouTubeAPI()
