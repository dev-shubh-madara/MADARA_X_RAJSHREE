"""
YouTube helper with a safe, optional download API and yt-dlp fallback.

This module keeps the public YouTubeAPI methods used by the original bot:
exists, url, details, title, duration, thumbnail, video, playlist, track,
formats, slider and download.

Environment variables:
    SHRUTI_API_URL   Optional download API base URL.
    SHRUTI_API_KEY   Optional API key. Never hard-code it in this file.
    DOWNLOAD_DIR     Optional download folder; defaults to downloads.

The custom API is attempted first when configured. If it returns an error,
JSON instead of media, or times out, yt-dlp is used as a local fallback.
"""

from __future__ import annotations

import asyncio
import glob
import json
import os
import re
from pathlib import Path
from typing import Any, Optional, Union

import aiohttp
import yt_dlp
from py_yt import Playlist, VideosSearch
from pyrogram.enums import MessageEntityType
from pyrogram.types import Message

try:
    from youtube_search import YoutubeSearch
except ImportError:
    YoutubeSearch = None


API_URL = os.environ.get("SHRUTI_API_URL", "").strip().rstrip("/")
API_KEY = os.environ.get("SHRUTI_API_KEY", "").strip()
DOWNLOAD_DIR = Path(os.environ.get("DOWNLOAD_DIR", "downloads"))


def time_to_seconds(value: Any) -> int:
    if value is None or value == "":
        return 0
    try:
        parts = str(value).strip().split(":")
        return sum(int(part) * 60 ** index for index, part in enumerate(reversed(parts)))
    except (TypeError, ValueError):
        return 0


def normalise_youtube_url(link: str) -> str:
    value = str(link or "").strip()
    if not value:
        return ""
    if re.fullmatch(r"[A-Za-z0-9_-]{6,}", value):
        return f"https://www.youtube.com/watch?v={value}"
    if value.startswith("youtu.be/"):
        return "https://" + value
    if value.startswith("youtube.com/"):
        return "https://www." + value
    return value


def youtube_video_id(link: str) -> str:
    value = normalise_youtube_url(link)
    patterns = (
        r"(?:v=)([A-Za-z0-9_-]{6,})",
        r"(?:youtu\.be/)([A-Za-z0-9_-]{6,})",
        r"(?:shorts/)([A-Za-z0-9_-]{6,})",
        r"(?:embed/)([A-Za-z0-9_-]{6,})",
    )
    for pattern in patterns:
        match = re.search(pattern, value)
        if match:
            return match.group(1)
    return value if re.fullmatch(r"[A-Za-z0-9_-]{6,}", value) else ""


def _safe_file_path(video_id: str, extension: str) -> Path:
    safe_id = re.sub(r"[^A-Za-z0-9_-]", "_", video_id) or "youtube_media"
    return DOWNLOAD_DIR / f"{safe_id}.{extension}"


def _api_headers() -> dict[str, str]:
    if not API_KEY:
        return {}
    return {
        "X-API-Key": API_KEY,
        "Authorization": f"Bearer {API_KEY}",
    }


def _api_params(link: str, media_type: str) -> dict[str, str]:
    params = {"url": link, "type": media_type}
    # Kept for compatibility with older versions of the custom API. The key
    # still comes only from the environment and is never stored in source.
    if API_KEY:
        params["api_key"] = API_KEY
    return params


async def _stream_to_file(
    session: aiohttp.ClientSession,
    url: str,
    destination: Path,
    headers: Optional[dict[str, str]] = None,
) -> Optional[Path]:
    async with session.get(
        url,
        headers=headers or {},
        timeout=aiohttp.ClientTimeout(total=900),
        allow_redirects=True,
    ) as response:
        if response.status != 200:
            return None
        content_type = (response.headers.get("Content-Type") or "").lower()
        if "json" in content_type or "text/html" in content_type:
            return None
        temporary = destination.with_suffix(destination.suffix + ".part")
        with temporary.open("wb") as output:
            async for chunk in response.content.iter_chunked(131072):
                if chunk:
                    output.write(chunk)
        if temporary.exists() and temporary.stat().st_size > 0:
            temporary.replace(destination)
            return destination
        temporary.unlink(missing_ok=True)
        return None


def _json_download_url(payload: Any) -> str:
    if not isinstance(payload, dict):
        return ""
    candidates: list[Any] = [
        payload.get("url"),
        payload.get("download_url"),
        payload.get("downloadUrl"),
        payload.get("file"),
    ]
    data = payload.get("data")
    if isinstance(data, dict):
        candidates.extend([data.get("url"), data.get("download_url"), data.get("file")])
    for candidate in candidates:
        if isinstance(candidate, str) and candidate.startswith(("http://", "https://")):
            return candidate
    return ""


async def _download_from_api(
    link: str, media_type: str, destination: Path
) -> Optional[Path]:
    if not API_URL:
        return None
    endpoint = f"{API_URL}/download"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                endpoint,
                params=_api_params(link, media_type),
                headers=_api_headers(),
                timeout=aiohttp.ClientTimeout(total=900),
            ) as response:
                if response.status != 200:
                    return None
                content_type = (response.headers.get("Content-Type") or "").lower()
                if "json" in content_type:
                    try:
                        payload = await response.json(content_type=None)
                    except (aiohttp.ContentTypeError, json.JSONDecodeError):
                        return None
                    download_url = _json_download_url(payload)
                    if not download_url:
                        return None
                    return await _stream_to_file(
                        session, download_url, destination, _api_headers()
                    )
                if "text/html" in content_type:
                    return None
                temporary = destination.with_suffix(destination.suffix + ".part")
                with temporary.open("wb") as output:
                    async for chunk in response.content.iter_chunked(131072):
                        if chunk:
                            output.write(chunk)
                if temporary.exists() and temporary.stat().st_size > 0:
                    temporary.replace(destination)
                    return destination
                temporary.unlink(missing_ok=True)
    except (aiohttp.ClientError, asyncio.TimeoutError, OSError):
        return None
    return None


async def _download_with_ytdlp(
    link: str, video_id: str, media_type: str, destination: Path
) -> Optional[Path]:
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    output_template = str(DOWNLOAD_DIR / f"{video_id}.%(ext)s")
    options: dict[str, Any] = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "outtmpl": output_template,
        "retries": 3,
        "fragment_retries": 3,
        "geo_bypass": True,
        "nocheckcertificate": True,
    }
    if media_type == "audio":
        options.update(
            {
                "format": "bestaudio/best",
                "postprocessors": [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "192",
                    }
                ],
            }
        )
    else:
        options["format"] = (
            "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"
        )
        options["merge_output_format"] = "mp4"

    try:
        def run_download() -> None:
            with yt_dlp.YoutubeDL(options) as downloader:
                downloader.download([link])

        await asyncio.to_thread(run_download)
    except Exception:
        return None

    if destination.exists() and destination.stat().st_size > 0:
        return destination
    candidates = [
        Path(path)
        for path in glob.glob(str(DOWNLOAD_DIR / f"{video_id}.*"))
        if not path.endswith(".part") and Path(path).is_file()
    ]
    candidates.sort(key=lambda path: path.stat().st_mtime, reverse=True)
    if candidates:
        newest = candidates[0]
        if newest != destination:
            try:
                newest.replace(destination)
            except OSError:
                return newest
        return destination if destination.exists() else newest
    return None


async def _download_media(link: str, media_type: str) -> Optional[str]:
    clean_link = normalise_youtube_url(link)
    video_id = youtube_video_id(clean_link)
    if not video_id:
        return None
    extension = "mp3" if media_type == "audio" else "mp4"
    destination = _safe_file_path(video_id, extension)
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    if destination.exists() and destination.stat().st_size > 0:
        return str(destination)

    api_result = await _download_from_api(clean_link, media_type, destination)
    if api_result:
        return str(api_result)
    local_result = await _download_with_ytdlp(
        clean_link, video_id, media_type, destination
    )
    return str(local_result) if local_result else None


async def download_song(link: str) -> Optional[str]:
    return await _download_media(link, "audio")


async def download_video(link: str) -> Optional[str]:
    return await _download_media(link, "video")


class YouTubeAPI:
    def __init__(self) -> None:
        self.base = "https://www.youtube.com/watch?v="
        self.regex = r"(?:youtube\.com|youtu\.be)"
        self.status = "https://www.youtube.com/oembed?url="
        self.listbase = "https://youtube.com/playlist?list="

    async def exists(self, link: str, videoid: Union[bool, str] = None) -> bool:
        value = self.base + str(link) if videoid else str(link or "")
        return bool(re.search(self.regex, value, re.IGNORECASE)) or bool(
            youtube_video_id(value)
        )

    async def url(self, message_1: Message) -> Optional[str]:
        messages = [message_1]
        if message_1.reply_to_message:
            messages.append(message_1.reply_to_message)
        for message in messages:
            text = message.text or message.caption or ""
            for entity in message.entities or message.caption_entities or []:
                entity_type = str(entity.type)
                if entity.type == MessageEntityType.TEXT_LINK and entity.url:
                    return entity.url
                if entity.type == MessageEntityType.URL:
                    # Telegram offsets are UTF-16; for normal ASCII URLs this
                    # slice is correct and is retained for compatibility.
                    return text[entity.offset : entity.offset + entity.length]
            match = re.search(
                r"https?://(?:www\.)?(?:youtube\.com|youtu\.be)/\S+",
                text,
                re.IGNORECASE,
            )
            if match:
                return match.group(0).rstrip(").,")
        return None

    async def _search(self, query: str) -> Optional[dict[str, Any]]:
        result: Optional[dict[str, Any]] = None
        lookup = query if re.search(self.regex, query, re.IGNORECASE) else f"ytsearch1:{query}"
        try:
            options = {
                "quiet": True,
                "no_warnings": True,
                "skip_download": True,
                "extract_flat": True,
                "noplaylist": True,
                "default_search": "ytsearch",
                "geo_bypass": True,
                "nocheckcertificate": True,
            }
            with yt_dlp.YoutubeDL(options) as downloader:
                info = await asyncio.to_thread(downloader.extract_info, lookup, False)
            entries = info.get("entries") if info else None
            result = (entries or [info])[0] if entries or info else None
        except Exception:
            result = None

        if result:
            return result
        try:
            search = VideosSearch(query, limit=1)
            response = await asyncio.wait_for(search.next(), timeout=30)
            results = response.get("result", []) if response else []
            return results[0] if results else None
        except Exception:
            return None

    @staticmethod
    def _track_dict(result: dict[str, Any], base: str) -> tuple[dict[str, Any], str]:
        video_id = result.get("id") or result.get("webpage_url", "").split("v=")[-1]
        title = result.get("title") or "Unknown title"
        if not video_id:
            raise RuntimeError("YouTube returned no video ID")
        duration_value = result.get("duration") or result.get("lengthSeconds") or 0
        if isinstance(duration_value, (int, float)):
            seconds = int(duration_value)
            hours, remainder = divmod(seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            duration = (
                f"{hours}:{minutes:02d}:{seconds:02d}"
                if hours
                else f"{minutes}:{seconds:02d}"
            )
        else:
            duration = str(duration_value)
        thumbnails = result.get("thumbnails") or []
        first = thumbnails[0] if thumbnails else ""
        thumbnail = first.get("url", "") if isinstance(first, dict) else str(first)
        details = {
            "title": title,
            "link": result.get("webpage_url")
            or result.get("webpage_url_basename")
            or result.get("link")
            or f"{base}{video_id}",
            "vidid": video_id,
            "duration_min": duration,
            "thumb": thumbnail.split("?", 1)[0],
        }
        return details, video_id

    async def details(self, link: str, videoid: Union[bool, str] = None):
        query = self.base + str(link) if videoid else normalise_youtube_url(link)
        result = await self._search(query)
        if not result:
            raise RuntimeError("YouTube returned no track details")
        details, _ = self._track_dict(result, self.base)
        return (
            details["title"],
            details["duration_min"],
            time_to_seconds(details["duration_min"]),
            details["thumb"],
            details["vidid"],
        )

    async def title(self, link: str, videoid: Union[bool, str] = None):
        return (await self.details(link, videoid))[0]

    async def duration(self, link: str, videoid: Union[bool, str] = None):
        return (await self.details(link, videoid))[1]

    async def thumbnail(self, link: str, videoid: Union[bool, str] = None):
        return (await self.details(link, videoid))[3]

    async def video(self, link: str, videoid: Union[bool, str] = None):
        query = self.base + str(link) if videoid else link
        downloaded = await download_video(query)
        return (1, downloaded) if downloaded else (0, "Video download failed")

    async def playlist(
        self, link: str, limit: int, user_id: Any, videoid: Union[bool, str] = None
    ):
        query = self.listbase + str(link) if videoid else link
        try:
            playlist = await Playlist.get(query)
            return [
                item.get("id")
                for item in (playlist.get("videos") or [])[:limit]
                if item and item.get("id")
            ]
        except Exception:
            return []

    async def track(self, link: str, videoid: Union[bool, str] = None):
        query = self.base + str(link) if videoid else str(link or "").strip()
        if not query:
            raise ValueError("Empty YouTube search query")
        result = await self._search(query)
        if not result:
            raise RuntimeError("YouTube search returned no track details")
        details, video_id = self._track_dict(result, self.base)
        return details, video_id

    async def formats(self, link: str, videoid: Union[bool, str] = None):
        query = self.base + str(link) if videoid else normalise_youtube_url(link)

        def read_formats() -> list[dict[str, Any]]:
            with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True}) as downloader:
                info = downloader.extract_info(query, download=False)
            values = []
            for item in info.get("formats", []):
                if "dash" in str(item.get("format", "")).lower():
                    continue
                values.append(
                    {
                        "format": item.get("format", ""),
                        "filesize": item.get("filesize"),
                        "format_id": item.get("format_id"),
                        "ext": item.get("ext"),
                        "format_note": item.get("format_note"),
                        "yturl": query,
                    }
                )
            return values

        return await asyncio.to_thread(read_formats), query

    async def slider(
        self, link: str, query_type: int, videoid: Union[bool, str] = None
    ):
        query = self.base + str(link) if videoid else link
        response = await asyncio.wait_for(
            VideosSearch(query, limit=10).next(), timeout=30
        )
        results = response.get("result") or []
        if query_type < 0 or query_type >= len(results):
            raise IndexError("YouTube search result index out of range")
        item = results[query_type]
        return (
            item["title"],
            item.get("duration") or "",
            item["thumbnails"][0]["url"].split("?")[0],
            item["id"],
        )

    async def download(
        self,
        link: str,
        mystic: Any,
        video: Union[bool, str] = None,
        videoid: Union[bool, str] = None,
        songaudio: Union[bool, str] = None,
        songvideo: Union[bool, str] = None,
        format_id: Union[bool, str] = None,
        title: Union[bool, str] = None,
    ):
        query = self.base + str(link) if videoid else link
        downloaded = await (download_video(query) if video else download_song(query))
        return (downloaded, True) if downloaded else (None, False)


YouTube = YouTubeAPI()
