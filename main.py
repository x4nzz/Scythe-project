import os
import re
import json
import time
import random
import asyncio
import sqlite3
import datetime
import urllib.request
import urllib.parse
from collections import defaultdict, deque
from typing import Optional, Union

import discord
from discord.ext import commands, tasks
from discord.ui import View, Button, Modal, TextInput, Select
import yt_dlp
import wavelink

# ==========================================
# CONFIGURATION & CONSTANTS
# ==========================================
BOT_TOKEN = os.getenv("DISCORD_TOKEN", "YOUR_BOT_TOKEN_HERE")
DB_NAME = "scyth_database.db"
EMBED_COLOR = 0x2b2d31
MUSIC_ICON_GIF = "https://i.imgur.com/vHqQo2U.gif"

# Regular expression to catch Discord invite links
INVITE_REGEX = re.compile(
    r"(https?:\/\/)?(www\.)?(discord\.(gg|io|me|li)|discord(?:app)?\.com\/invite)\/[a-zA-Z0-9\-]+",
    re.IGNORECASE,
)

# Custom Application Emojis
EMOJI_PENCIL = "<:pencil:1558976150900973631>"
EMOJI_STAR = "<:star:1558975756019834881>"
EMOJI_BELL = "<:bell:1558975291999649934>"
EMOJI_CHAINLINK = "<:chainlink:1558975011031752735>"
EMOJI_TRASH = "<:trash:1558974738469101708>"
EMOJI_CLOCK = "<:clock:1558973824148570163>"
EMOJI_CROSS = "<:cross:1558973516995629146>"
EMOJI_CHECKMARK = "<:checkmark:1558973325005561969>"
EMOJI_HAMMER = "<:hammer:1558973163545559141>"

EMOJI_INFO = "<:info:1558955788980981830>"
EMOJI_INCREASE = "<:increase:1558955787861364876>"
EMOJI_DECREASE = "<:decrease:1558955786946748457>"
EMOJI_CLAIM = "<:claim:1558955785810350210>"
EMOJI_DISCONNECT = "<:disconnect:1558955784723763320>"
EMOJI_ACTIVITY = "<:activity:1558955783855538238>"
EMOJI_UNGHOST = "<:unghost:1558955782475751424>"
EMOJI_GHOST = "<:ghost:1558955780898689094>"
EMOJI_UNLOCK = "<:unlock:1558955779372089437>"
EMOJI_LOCK = "<:lock:1558955778470055986>"
EMOJI_GEARSET = "<:gearset:1559040485245452338>"
EMOJI_SPEAKER = "<:speaker:1559040182991454298>"
EMOJI_DISC = "<:disc:1559039580286484551>"
EMOJI_SHIELD = "<:shield:1559039291349409822>"

# In-Memory Security & Rate-Limit Trackers
antinuke_tracker = defaultdict(lambda: defaultdict(deque))
raid_tracker = defaultdict(deque)
spam_tracker = defaultdict(deque)

# Cache structures
sniped_messages = {}
edited_messages = {}

# Replace with your main server's ID
MAIN_GUILD_ID = 1531895848177500200  

async def update_music_presence(track: Optional[Union[wavelink.Playable, str]] = None):
    """Sets a clean, aesthetic 'Listening to' status matching top music bots."""
    if track:
        if isinstance(track, str):
            status_text = track
        else:
            clean_title = re.sub(r'\(.*?\)|\[.*?\]', '', track.title).strip()
            artist = getattr(track, "author", "")
            status_text = f"{clean_title} • {artist}" if artist else clean_title

        if len(status_text) > 128:
            status_text = status_text[:125] + "..."

        await bot.change_presence(
            activity=discord.Activity(type=discord.ActivityType.listening, name=status_text)
        )
    else:
        await bot.change_presence(
            activity=discord.Activity(type=discord.ActivityType.watching, name="scyth security")
        )

# ==========================================
# YT-DLP & AUDIO ENGINE CONFIGURATION
# ==========================================
DENO_PATH = os.path.expanduser("~/.deno/bin/deno")

YTDL_OPTIONS = {
    "format": "bestaudio/best",
    "restrictfilenames": True,
    "noplaylist": True,
    "nocheckcertificate": True,
    "ignoreerrors": False,
    "logtostderr": False,
    "quiet": True,
    "no_warnings": True,
    "default_search": "ytsearch",
    "source_address": "0.0.0.0",
}

if os.path.exists(DENO_PATH):
    YTDL_OPTIONS["js_runtimes"] = {"deno": {"path": DENO_PATH}}

if os.path.exists("cookies.txt"):
    YTDL_OPTIONS["cookiefile"] = "cookies.txt"

FFMPEG_OPTIONS = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": "-vn",
}

ytdl = yt_dlp.YoutubeDL(YTDL_OPTIONS)

def format_duration(seconds: int) -> str:
    if not seconds:
        return "Live / Unknown"
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"

async def get_spotify_web_token():
    """Fetches an anonymous Spotify Web Player token to paginate beyond 100 songs."""
    req = urllib.request.Request(
        "https://open.spotify.com/get_access_token",
        headers={"User-Agent": "Mozilla/5.0"}
    )
    def fetch():
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode())
                return data.get("accessToken")
        except Exception:
            return None
    return await asyncio.to_thread(fetch)

async def resolve_spotify_track(url: str):
    """Resolves Spotify URLs to searchable track titles and artwork via public oEmbed."""
    try:
        req = urllib.request.Request(
            f"https://open.spotify.com/oembed?url={url}",
            headers={"User-Agent": "Mozilla/5.0"}
        )
        def fetch():
            with urllib.request.urlopen(req, timeout=5) as response:
                return json.loads(response.read().decode())
        data = await asyncio.to_thread(fetch)
        title = data.get("title")
        thumbnail = data.get("thumbnail_url")
        return f"{title}", thumbnail
    except Exception:
        return None, None

async def resolve_spotify_playlist(url: str, offset: int = 0):
    """Loads Spotify playlist tracks in 100-song batches with full pagination support."""
    m = re.search(r'spotify\.com/(?:embed/)?(playlist|album)/([a-zA-Z0-9]+)', url)
    if not m:
        return [], None, None, 0

    entity_type, entity_id = m.group(1), m.group(2)

    if offset == 0:
        embed_url = f"https://open.spotify.com/embed/{entity_type}/{entity_id}"
        req = urllib.request.Request(embed_url, headers={"User-Agent": "Mozilla/5.0"})

        def fetch_embed():
            try:
                with urllib.request.urlopen(req, timeout=8) as resp:
                    html = resp.read().decode("utf-8")
                    match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html)
                    if match:
                        data = json.loads(match.group(1))
                        entity = data.get("props", {}).get("pageProps", {}).get("state", {}).get("data", {}).get("entity", {})
                        track_list = entity.get("trackList", [])
                        name = entity.get("name", "Spotify Playlist")
                        cover = entity.get("coverArt", {}).get("sources", [{}])[0].get("url")
                        
                        queries = []
                        for t in track_list:
                            title = t.get("title")
                            subtitle = t.get("subtitle")
                            if title:
                                queries.append(f"{subtitle} - {title}" if subtitle else title)
                        return queries, name, cover
            except Exception as e:
                print(f"[Spotify Embed Error]: {e}")
            return [], None, None

        queries, name, cover = await asyncio.to_thread(fetch_embed)
        return queries, name, cover, len(queries)

    token = await get_spotify_web_token()
    if not token:
        return [], None, None, 0

    api_url = f"https://api.spotify.com/v1/{entity_type}s/{entity_id}/tracks?offset={offset}&limit=100"
    req = urllib.request.Request(
        api_url,
        headers={"Authorization": f"Bearer {token}", "User-Agent": "Mozilla/5.0"}
    )

    def fetch_api():
        try:
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode())
                items = data.get("items", [])
                queries = []
                for item in items:
                    track = item.get("track", item)
                    if track and track.get("name"):
                        artists = ", ".join([a["name"] for a in track.get("artists", [])])
                        queries.append(f"{artists} - {track['name']}" if artists else track["name"])
                return queries, len(queries)
        except Exception as e:
            print(f"[Spotify Page {offset//100 + 1} Error]: {e}")
            return [], 0

    queries, total = await asyncio.to_thread(fetch_api)
    return queries, None, None, total

class LoadMoreTracksView(View):
    def __init__(self, playlist_url: str, current_page: int, requester: discord.Member, manager, pl_name: str, pl_thumb: str):
        super().__init__(timeout=300)
        self.playlist_url = playlist_url
        self.page = current_page
        self.requester = requester
        self.manager = manager
        self.pl_name = pl_name
        self.pl_thumb = pl_thumb
        self.update_button_label()

    def update_button_label(self):
        self.load_button.label = f"Load Next 100 (Page {self.page + 1})"

    @discord.ui.button(label="Load Next 100 (Page 2)", style=discord.ButtonStyle.secondary, emoji="➕")
    async def load_button(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.requester.id and not interaction.user.guild_permissions.manage_channels:
            return await interaction.response.send_message("Only the person who queued this playlist can load more pages.", ephemeral=True)

        await interaction.response.defer()
        next_offset = self.page * 100
        queries, _, _, count = await resolve_spotify_playlist(self.playlist_url, offset=next_offset)

        if not queries:
            button.disabled = True
            button.label = "All Tracks Loaded"
            await interaction.message.edit(view=self)
            return await interaction.followup.send(f"{EMOJI_CHECKMARK} All songs from **{self.pl_name}** are now in the queue!", ephemeral=True)

        self.page += 1
        self.update_button_label()
        if count < 100:
            button.disabled = True
            button.label = "All Tracks Loaded"

        await interaction.message.edit(view=self)

        self.manager.loader_task = asyncio.create_task(
            load_remaining_playlist_tracks(self.manager, queries, self.requester)
        )

        embed = discord.Embed(
            description=f"{EMOJI_CHECKMARK} Queued **{len(queries)}** more tracks from **{self.pl_name}** (Page {self.page}).",
            color=EMBED_COLOR
        )
        embed.set_footer(text="scyth • music", icon_url=bot.user.display_avatar.url)
        await interaction.followup.send(embed=embed)

async def load_remaining_playlist_tracks(manager, queries: list, requester: discord.Member):
    for q in queries:
        try:
            data = await fetch_track_data(q)
            if data:
                manager.queue.append(Track(data, requester))
                if not manager.voice_client or not manager.voice_client.is_connected():
                    break
                if not manager.voice_client.is_playing() and not manager.voice_client.is_paused():
                    manager.play_next()
        except Exception:
            continue

flat_ytdl = yt_dlp.YoutubeDL({
    "extract_flat": True,
    "quiet": True,
    "no_warnings": True,
    "source_address": "0.0.0.0",
})

UNWANTED_MODIFIERS = [
    "slowed", "slow", "sped up", "speed up", "spedup", "nightcore",
    "reverb", "chopped", "bass boost", "bassboost", "earrape",
    "live at", "rolling loud", "concert", "tribute", "cover", "karaoke",
    "type beat", "remake", "instrumental"
]

async def fetch_track_data(query: str):
    loop = asyncio.get_event_loop()
    clean_query = query.replace("scsearch:", "").replace("ytsearch:", "").strip()
    query_lower = clean_query.lower()

    if "soundcloud.com/" in query or "youtube.com/" in query or "youtu.be/" in query:
        try:
            data = await loop.run_in_executor(None, lambda: ytdl.extract_info(query, download=False))
            if data and data.get("url"):
                return data
        except Exception:
            pass

    try:
        search_results = await loop.run_in_executor(
            None, lambda: flat_ytdl.extract_info(f"scsearch12:{clean_query}", download=False)
        )
        entries = search_results.get("entries", []) if search_results else []
    except Exception as e:
        print(f"[Search Query Error]: {e}")
        entries = []

    for entry in entries:
        if not entry:
            continue
        title = entry.get("title", "")
        title_lower = title.lower()

        if any(mod in title_lower and mod not in query_lower for mod in UNWANTED_MODIFIERS):
            continue

        track_url = entry.get("url") or entry.get("webpage_url")
        if not track_url:
            continue

        try:
            track_data = await loop.run_in_executor(
                None, lambda: ytdl.extract_info(track_url, download=False)
            )
            if track_data and track_data.get("url"):
                duration = track_data.get("duration", 0)
                if duration == 30:
                    continue
                return track_data
        except Exception:
            continue

    STRICT_SPEED_LOCKS = ["slowed", "sped up", "speed up", "spedup", "nightcore", "chopped"]
    for entry in entries:
        if not entry:
            continue
        title_lower = entry.get("title", "").lower()
        if any(mod in title_lower and mod not in query_lower for mod in STRICT_SPEED_LOCKS):
            continue

        track_url = entry.get("url") or entry.get("webpage_url")
        if not track_url:
            continue

        try:
            track_data = await loop.run_in_executor(
                None, lambda: ytdl.extract_info(track_url, download=False)
            )
            if track_data and track_data.get("url") and track_data.get("duration", 0) != 30:
                return track_data
        except Exception:
            continue

    return None

# ==========================================
# CENTRALIZED COMMAND SYNTAX REPOSITORY
# ==========================================
COMMAND_SYNTAX = {
    "ban": {
        "title": "Ban Command",
        "desc": "Bans a specified member from the server.",
        "usage": ["• `!ban <member> [reason]` — Ban a user from the guild."]
    },
    "unban": {
        "title": "Unban Command",
        "desc": "Unbans a user using their Discord account ID.",
        "usage": ["• `!unban <user_id> [reason]` — Unban a user from the guild."]
    },
    "kick": {
        "title": "Kick Command",
        "desc": "Kicks a specified member from the server.",
        "usage": ["• `!kick <member> [reason]` — Kick a member from the guild."]
    },
    "timeout": {
        "title": "Timeout Command",
        "desc": "Mutes/times out a member for a given duration.",
        "usage": ["• `!timeout <member> <minutes> [reason]` — Timeout a member (1-40320 mins)."]
    },
    "untimeout": {
        "title": "Untimeout Command",
        "desc": "Removes a timeout from a timed-out member.",
        "usage": ["• `!untimeout <member> [reason]` — Remove an active timeout."]
    },
    "warn": {
        "title": "Warn Command",
        "desc": "Logs a formal moderation warning for a member.",
        "usage": ["• `!warn <member> [reason]` — Warn a member in the server."]
    },
    "warnings": {
        "title": "Warnings Command",
        "desc": "Displays all recorded warnings for a member.",
        "usage": ["• `!warnings <member>` — View warnings for a member."]
    },
    "clearwarnings": {
        "title": "Clear Warnings Command",
        "desc": "Clears all recorded warnings for a member.",
        "usage": ["• `!clearwarnings <member>` — Clear all warnings for a member."]
    },
    "purge": {
        "title": "Purge Command",
        "desc": "Deletes a specified number of recent messages from the channel.",
        "usage": ["• `!purge <1-100>` — Purge chat history."]
    },
    "embed": {
        "title": "Embed Command",
        "desc": "Sends a custom formatted embed message.",
        "usage": ["• `!embed <title> | <description> | [hex_color]` — Send a custom embed."]
    },
    "nuke": {
        "title": "Nuke Command",
        "desc": "Clones and deletes the current channel to wipe chat history.",
        "usage": ["• `!nuke` — Reset and wipe the current channel."]
    },
    "autonuke": {
        "title": "Auto-Nuke Commands",
        "desc": "Automatically wipe a channel's history on a repeating timer.",
        "usage": [
            "• `!autonuke set <minutes>` — Enable auto-nuke for this channel.",
            "• `!autonuke remove` — Disable auto-nuke for this channel."
        ]
    },
    "voicemaster": {
        "title": "VoiceMaster Commands",
        "desc": "Configure the dynamic voice channel and interface panel.",
        "usage": ["• `!voicemaster setup` — Configure the VoiceMaster category and interface."]
    },
    "serverinfo": {
        "title": "Server Info Command",
        "desc": "Displays detailed statistics about the current server.",
        "usage": ["• `!serverinfo` — View server statistics."]
    },
    "channelinfo": {
        "title": "Channel Info Command",
        "desc": "Displays information about a text channel.",
        "usage": ["• `!channelinfo [channel]` — View channel information."]
    },
    "userinfo": {
        "title": "User Info Command",
        "desc": "Displays detailed profile information about a member or yourself.",
        "usage": ["• `!userinfo [member]` — View user profile details."]
    },
    "snipe": {
        "title": "Snipe Command",
        "desc": "Snipes the most recently deleted message in this channel.",
        "usage": ["• `!snipe` — Retrieve the last deleted message."]
    },
    "editsnipe": {
        "title": "Edit Snipe Command",
        "desc": "Snipes the pre-edited version of the last modified message.",
        "usage": ["• `!editsnipe` — Retrieve the last edited message."]
    },
    "clearsnipe": {
        "title": "Clear Snipe Command",
        "desc": "Purges cached deleted and edited messages from this channel.",
        "usage": ["• `!clearsnipe` — Wipe cached snipes."]
    },
    "afk": {
        "title": "AFK Command",
        "desc": "Sets your status to away from keyboard with an optional reason.",
        "usage": ["• `!afk [reason]` — Set your AFK message."]
    },
    "play": {
        "title": "Play Command",
        "desc": "Plays audio from YouTube, SoundCloud, Spotify, or Deezer.",
        "usage": ["• `!play <song name or link>` — Queue a track to stream."]
    },
    "playnext": {
        "title": "Play Next Command",
        "desc": "Inserts a track straight to the very front of the audio queue.",
        "usage": ["• `!playnext <song name or link>` — Prioritize track next in queue."]
    },
    "queue": {
        "title": "Queue Command",
        "desc": "Displays the list of upcoming tracks.",
        "usage": ["• `!queue` — View server music queue."]
    },
    "volume": {
        "title": "Volume Command",
        "desc": "Adjusts music playback volume percentage.",
        "usage": ["• `!volume <1-100>` — Change playback loudness."]
    },
    "autoplay": {
        "title": "Autoplay Command",
        "desc": "Toggles automatic playback of recommended songs when the queue runs out.",
        "usage": ["• `!autoplay` — Toggle autoplay on or off."]
    },
    "lock": {
        "title": "Lock Command",
        "desc": "Locks the current text channel to prevent members from sending messages.",
        "usage": ["• `!lock` — Lock the current text channel."]
    },
    "unlock": {
        "title": "Unlock Command",
        "desc": "Unlocks the current text channel to allow members to send messages again.",
        "usage": ["• `!unlock` — Unlock the current text channel."]
    },
    "pause": {
        "title": "Pause Command",
        "desc": "Pauses the currently playing audio stream.",
        "usage": ["• `!pause` — Pause current track."]
    },
    "resume": {
        "title": "Resume Command",
        "desc": "Resumes audio playback if currently paused.",
        "usage": ["• `!resume` — Resume playback."]
    },
    "jail": {
        "title": "Jail Command",
        "desc": "Isolates a member to the jail channel and preserves their existing roles.",
        "usage": ["• `!jail <member> [reason]` — Send member to jail."]
    },
    "unjail": {
        "title": "Unjail Command",
        "desc": "Restores original roles to a jailed member and releases them.",
        "usage": ["• `!unjail <member>` — Release member from jail."]
    },
    "strip": {
        "title": "Strip Command",
        "desc": "Strips all custom roles from a user and saves them for quick restoration.",
        "usage": ["• `!strip <member> [reason]` — Strip all custom roles."]
    },
    "restore": {
        "title": "Restore Command",
        "desc": "Restores previously stripped roles to a member.",
        "usage": ["• `!restore <member>` — Return stripped roles."]
    },
    "hardban": {
        "title": "Hardban Command",
        "desc": "Bans a user and adds them to a persistent SQLite blacklist.",
        "usage": ["• `!hardban <user_id> [reason]` — Permanently blacklist and ban a user."]
    },
    "fakeperms": {
        "title": "Fake Permissions Commands",
        "desc": "Grant specific roles permission to use bot commands without admin access.",
        "usage": [
            "• `!fakeperms add <@role> <command>` — Grant role permission.",
            "• `!fakeperms remove <@role> <command>` — Revoke role permission.",
            "• `!fakeperms list` — View all fake permission mappings."
        ]
    },
    "autoresponder": {
        "title": "Autoresponder Commands",
        "desc": "Configure custom automated message responses.",
        "usage": [
            "• `!ar add <trigger> | <response>` — Create custom trigger.",
            "• `!ar remove <trigger>` — Delete trigger.",
            "• `!ar list` — View all active triggers."
        ]
    },
    "avatar": {
        "title": "Avatar Command",
        "desc": "Displays a member's global profile avatar.",
        "usage": ["• `!avatar [member]` — View avatar."]
    },
    "banner": {
        "title": "Banner Command",
        "desc": "Displays a user's custom profile banner.",
        "usage": ["• `!banner [user]` — View profile banner."]
    },
    "firstmessage": {
        "title": "First Message Command",
        "desc": "Finds and links to the very first message sent in this channel.",
        "usage": ["• `!firstmessage` — Get link to first message."]
    },
    "mediaonly": {
        "title": "Media Only Command",
        "desc": "Enforces media-only attachments in a text channel.",
        "usage": ["• `!mediaonly` — Toggle media enforcement for this channel."]
    },
    "role": {
        "title": "Role Command",
        "desc": "Toggles or grants a role to a member.",
        "usage": ["• `!role <member> <role>` — Add or remove a role."]
    },
    "membercount": {
        "title": "Member Count Command",
        "desc": "Displays clean server member count statistics.",
        "usage": ["• `!membercount` — View server counts."]
    }
}

def get_syntax_embed(command_name: str) -> Optional[discord.Embed]:
    info = COMMAND_SYNTAX.get(command_name.lower())
    if not info:
        return None
    lines = "\n".join(info["usage"])
    embed = discord.Embed(
        title=info["title"],
        description=f"{info['desc']}\n\n{lines}",
        color=EMBED_COLOR
    )
    embed.set_footer(text="scyth • syntax")
    return embed

# ==========================================
# DATABASE LAYER (SQLite3)
# ==========================================
def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mod_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER,
                action TEXT,
                target_id INTEGER,
                moderator_id INTEGER,
                reason TEXT,
                timestamp TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS warnings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER,
                user_id INTEGER,
                moderator_id INTEGER,
                reason TEXT,
                timestamp TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vm_config (
                guild_id INTEGER PRIMARY KEY,
                category_id INTEGER,
                jtc_channel_id INTEGER,
                interface_channel_id INTEGER
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vm_channels (
                channel_id INTEGER PRIMARY KEY,
                guild_id INTEGER,
                owner_id INTEGER
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scheduled_nukes (
                channel_id INTEGER PRIMARY KEY,
                guild_id INTEGER,
                wipe_interval_seconds INTEGER,
                next_wipe_timestamp REAL
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS afk_users (
                user_id INTEGER,
                guild_id INTEGER,
                reason TEXT,
                timestamp REAL,
                PRIMARY KEY (user_id, guild_id)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS jailed_users (
                guild_id INTEGER,
                user_id INTEGER,
                role_ids TEXT,
                PRIMARY KEY (guild_id, user_id)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stripped_users (
                guild_id INTEGER,
                user_id INTEGER,
                role_ids TEXT,
                PRIMARY KEY (guild_id, user_id)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS hardbans (
                guild_id INTEGER,
                user_id INTEGER,
                reason TEXT,
                PRIMARY KEY (guild_id, user_id)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS fake_permissions (
                guild_id INTEGER,
                role_id INTEGER,
                command_name TEXT,
                PRIMARY KEY (guild_id, role_id, command_name)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS autoresponders (
                guild_id INTEGER,
                trigger TEXT,
                response TEXT,
                PRIMARY KEY (guild_id, trigger)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS media_only_channels (
                guild_id INTEGER,
                channel_id INTEGER,
                PRIMARY KEY (guild_id, channel_id)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS active_playback (
                guild_id INTEGER PRIMARY KEY,
                title TEXT,
                artist TEXT,
                uri TEXT,
                artwork TEXT,
                duration INTEGER,
                started_at REAL,
                is_playing INTEGER
            )
        """)
        conn.commit()

def log_mod_action(guild_id: int, action: str, target_id: int, moderator_id: int, reason: str):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        timestamp = datetime.datetime.utcnow().isoformat()
        cursor.execute(
            "INSERT INTO mod_logs (guild_id, action, target_id, moderator_id, reason, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
            (guild_id, action, target_id, moderator_id, reason, timestamp)
        )
        conn.commit()

def add_warning(guild_id: int, user_id: int, moderator_id: int, reason: str):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        timestamp = datetime.datetime.utcnow().isoformat()
        cursor.execute(
            "INSERT INTO warnings (guild_id, user_id, moderator_id, reason, timestamp) VALUES (?, ?, ?, ?, ?)",
            (guild_id, user_id, moderator_id, reason, timestamp)
        )
        conn.commit()

def get_warnings(guild_id: int, user_id: int):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, moderator_id, reason, timestamp FROM warnings WHERE guild_id = ? AND user_id = ?", (guild_id, user_id))
        return cursor.fetchall()

def clear_warnings(guild_id: int, user_id: int) -> int:
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM warnings WHERE guild_id = ? AND user_id = ?", (guild_id, user_id))
        conn.commit()
        return cursor.rowcount

def save_vm_config(guild_id: int, category_id: int, jtc_id: int, interface_id: int):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO vm_config (guild_id, category_id, jtc_channel_id, interface_channel_id)
            VALUES (?, ?, ?, ?)
        """, (guild_id, category_id, jtc_id, interface_id))
        conn.commit()

def get_vm_config(guild_id: int):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT category_id, jtc_channel_id, interface_channel_id FROM vm_config WHERE guild_id = ?", (guild_id,))
        return cursor.fetchone()

def add_temp_channel(channel_id: int, guild_id: int, owner_id: int):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO vm_channels (channel_id, guild_id, owner_id) VALUES (?, ?, ?)", (channel_id, guild_id, owner_id))
        conn.commit()

def get_temp_channel_owner(channel_id: int):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT owner_id FROM vm_channels WHERE channel_id = ?", (channel_id,))
        row = cursor.fetchone()
        return row[0] if row else None

def set_temp_channel_owner(channel_id: int, new_owner_id: int):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE vm_channels SET owner_id = ? WHERE channel_id = ?", (new_owner_id, channel_id))
        conn.commit()

def remove_temp_channel(channel_id: int):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM vm_channels WHERE channel_id = ?", (channel_id,))
        conn.commit()

def set_afk_status(user_id: int, guild_id: int, reason: str):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO afk_users (user_id, guild_id, reason, timestamp) VALUES (?, ?, ?, ?)",
            (user_id, guild_id, reason, time.time())
        )
        conn.commit()

def get_afk_status(user_id: int, guild_id: int):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT reason, timestamp FROM afk_users WHERE user_id = ? AND guild_id = ?", (user_id, guild_id))
        return cursor.fetchone()

def remove_afk_status(user_id: int, guild_id: int) -> bool:
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM afk_users WHERE user_id = ? AND guild_id = ?", (user_id, guild_id))
        conn.commit()
        return cursor.rowcount > 0

# ==========================================
# FAKE PERMISSIONS CHECK HELPER
# ==========================================
def has_permission_or_fake(discord_perm: str = None):
    async def predicate(ctx: commands.Context):
        if ctx.author.id == ctx.guild.owner_id or ctx.author.guild_permissions.administrator:
            return True
        if discord_perm and getattr(ctx.author.guild_permissions, discord_perm, False):
            return True
        role_ids = [r.id for r in ctx.author.roles]
        if role_ids:
            with sqlite3.connect(DB_NAME) as conn:
                cursor = conn.cursor()
                placeholders = ",".join("?" for _ in role_ids)
                cmd_name = ctx.command.qualified_name.split()[0].lower()
                cursor.execute(
                    f"SELECT 1 FROM fake_permissions WHERE guild_id = ? AND command_name = ? AND role_id IN ({placeholders})",
                    (ctx.guild.id, cmd_name, *role_ids)
                )
                if cursor.fetchone():
                    return True
        raise commands.MissingPermissions([discord_perm or f"FakePerm: {ctx.command.name}"])
    return commands.check(predicate)

# ==========================================
# MUSIC PLAYER INFRASTRUCTURE
# ==========================================
class Track:
    def __init__(self, data: dict, requester: discord.Member, override_thumb: str = None):
        self.title = data.get("title", "Unknown Title")
        self.webpage_url = data.get("webpage_url", "https://discord.com")
        self.stream_url = data.get("url")
        self.duration = data.get("duration", 0)
        self.thumbnail = override_thumb or data.get("thumbnail") or MUSIC_ICON_GIF
        self.uploader = data.get("uploader", "Unknown Artist")
        self.requester = requester

class GuildMusicManager:
    def __init__(self, guild_id: int):
        self.guild_id = guild_id
        self.queue = deque()
        self.current: Optional[Track] = None
        self.last_track: Optional[Track] = None
        self.voice_client: Optional[discord.VoiceClient] = None
        self.volume: float = 1.0
        self.loop: bool = False
        self.autoplay: bool = False
        self.history: deque = deque(maxlen=30)
        self.text_channel: Optional[discord.TextChannel] = None
        self.inactivity_task: Optional[asyncio.Task] = None
        self.loader_task: Optional[asyncio.Task] = None

    def cancel_loader(self):
        if self.loader_task and not self.loader_task.done():
            self.loader_task.cancel()
        self.loader_task = None

    def cancel_inactivity(self):
        if self.inactivity_task and not self.inactivity_task.done():
            self.inactivity_task.cancel()
        self.inactivity_task = None

    def start_inactivity(self):
        self.cancel_inactivity()
        self.inactivity_task = asyncio.create_task(self._inactivity_countdown())

    async def _inactivity_countdown(self):
        try:
            await asyncio.sleep(300)
            if not self.current and not self.queue:
                if self.voice_client and self.voice_client.is_connected():
                    await self.voice_client.disconnect()
                    self.voice_client = None
                    if self.text_channel:
                        embed = discord.Embed(
                            description=f"{EMOJI_CLOCK} Left the voice channel — no music has been played in the last 5 minutes.",
                            color=EMBED_COLOR
                        )
                        embed.set_footer(text="scyth • music", icon_url=bot.user.display_avatar.url)
                        await self.text_channel.send(embed=embed)
        except asyncio.CancelledError:
            pass

music_managers = {}

def get_manager(guild_id: int) -> GuildMusicManager:
    if guild_id not in music_managers:
        music_managers[guild_id] = GuildMusicManager(guild_id)
    return music_managers[guild_id]

# ==========================================
# VOICEMASTER COMPONENTS (MODALS, SELECTS, VIEW)
# ==========================================
class DisconnectMemberSelect(Select):
    def __init__(self, channel: discord.VoiceChannel):
        self.channel = channel
        options = [
            discord.SelectOption(label=m.display_name[:25], value=str(m.id), description=f"ID: {m.id}")
            for m in channel.members if not m.bot
        ]
        if not options:
            options = [discord.SelectOption(label="No members to disconnect", value="none")]

        super().__init__(placeholder="Select a member to disconnect...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "none":
            return await interaction.response.send_message(f"{EMOJI_CROSS} No eligible members to disconnect.", ephemeral=True)

        target_id = int(self.values[0])
        member = interaction.guild.get_member(target_id)
        if member and member in self.channel.members:
            await member.move_to(None, reason="Disconnected by voice channel owner")
            await interaction.response.send_message(f"{EMOJI_CHECKMARK} Disconnected **{member.display_name}**.", ephemeral=True)
        else:
            await interaction.response.send_message(f"{EMOJI_CROSS} Member is no longer connected to this channel.", ephemeral=True)

class DisconnectView(View):
    def __init__(self, channel: discord.VoiceChannel):
        super().__init__(timeout=60)
        self.add_item(DisconnectMemberSelect(channel))

class VoiceMasterInterface(View):
    def __init__(self):
        super().__init__(timeout=None)

    async def validate_user_channel(self, interaction: discord.Interaction, allow_non_owner: bool = False):
        voice_state = interaction.user.voice
        if not voice_state or not voice_state.channel:
            await interaction.response.send_message(f"{EMOJI_CROSS} You must be connected to your voice channel to manage it.", ephemeral=True)
            return None, None

        channel = voice_state.channel
        owner_id = get_temp_channel_owner(channel.id)

        if not owner_id:
            await interaction.response.send_message(f"{EMOJI_CROSS} You are not inside a managed voice channel.", ephemeral=True)
            return None, None

        if not allow_non_owner and interaction.user.id != owner_id:
            await interaction.response.send_message(f"{EMOJI_CROSS} Only the voice channel owner can use this control.", ephemeral=True)
            return None, None

        return channel, owner_id

    @discord.ui.button(emoji=EMOJI_LOCK, style=discord.ButtonStyle.secondary, custom_id="vm_lock", row=0)
    async def lock_channel(self, interaction: discord.Interaction, button: Button):
        channel, _ = await self.validate_user_channel(interaction)
        if not channel:
            return
        await channel.set_permissions(interaction.guild.default_role, connect=False)
        await interaction.response.send_message(f"{EMOJI_CHECKMARK} Locked your voice channel.", ephemeral=True)

    @discord.ui.button(emoji=EMOJI_UNLOCK, style=discord.ButtonStyle.secondary, custom_id="vm_unlock", row=0)
    async def unlock_channel(self, interaction: discord.Interaction, button: Button):
        channel, _ = await self.validate_user_channel(interaction)
        if not channel:
            return
        await channel.set_permissions(interaction.guild.default_role, connect=True)
        await interaction.response.send_message(f"{EMOJI_CHECKMARK} Unlocked your voice channel.", ephemeral=True)

    @discord.ui.button(emoji=EMOJI_GHOST, style=discord.ButtonStyle.secondary, custom_id="vm_ghost", row=0)
    async def ghost_channel(self, interaction: discord.Interaction, button: Button):
        channel, _ = await self.validate_user_channel(interaction)
        if not channel:
            return
        await channel.set_permissions(interaction.guild.default_role, view_channel=False)
        await interaction.response.send_message(f"{EMOJI_CHECKMARK} Your voice channel is now hidden.", ephemeral=True)

    @discord.ui.button(emoji=EMOJI_UNGHOST, style=discord.ButtonStyle.secondary, custom_id="vm_unghost", row=0)
    async def unghost_channel(self, interaction: discord.Interaction, button: Button):
        channel, _ = await self.validate_user_channel(interaction)
        if not channel:
            return
        await channel.set_permissions(interaction.guild.default_role, view_channel=True)
        await interaction.response.send_message(f"{EMOJI_CHECKMARK} Your voice channel is now visible.", ephemeral=True)

    @discord.ui.button(emoji=EMOJI_CLAIM, style=discord.ButtonStyle.secondary, custom_id="vm_claim", row=0)
    async def claim_channel(self, interaction: discord.Interaction, button: Button):
        channel, current_owner_id = await self.validate_user_channel(interaction, allow_non_owner=True)
        if not channel:
            return

        if interaction.user.id == current_owner_id:
            return await interaction.response.send_message(f"{EMOJI_CROSS} You are already the channel owner.", ephemeral=True)

        if any(m.id == current_owner_id for m in channel.members):
            return await interaction.response.send_message(f"{EMOJI_CROSS} You cannot claim while the current owner is still connected.", ephemeral=True)

        set_temp_channel_owner(channel.id, interaction.user.id)
        await interaction.response.send_message(f"{EMOJI_CHECKMARK} Claimed ownership of **{channel.name}**.", ephemeral=True)

    @discord.ui.button(emoji=EMOJI_DISCONNECT, style=discord.ButtonStyle.secondary, custom_id="vm_disconnect", row=1)
    async def disconnect_member(self, interaction: discord.Interaction, button: Button):
        channel, _ = await self.validate_user_channel(interaction)
        if not channel:
            return
        await interaction.response.send_message("Select a member to disconnect:", view=DisconnectView(channel), ephemeral=True)

    @discord.ui.button(emoji=EMOJI_ACTIVITY, style=discord.ButtonStyle.secondary, custom_id="vm_activity", row=1)
    async def start_activity(self, interaction: discord.Interaction, button: Button):
        channel, _ = await self.validate_user_channel(interaction, allow_non_owner=True)
        if not channel:
            return
        try:
            invite = await channel.create_invite(
                target_type=discord.InviteTarget.embedded_application,
                target_application_id=880218394199220274,
                max_age=300
            )
            await interaction.response.send_message(f"{EMOJI_CHAINLINK} Click here to launch Watch Together: {invite.url}", ephemeral=True)
        except Exception:
            await interaction.response.send_message(f"{EMOJI_CROSS} Unable to launch activity in this channel.", ephemeral=True)

    @discord.ui.button(emoji=EMOJI_INCREASE, style=discord.ButtonStyle.secondary, custom_id="vm_increase", row=1)
    async def increase_limit(self, interaction: discord.Interaction, button: Button):
        channel, _ = await self.validate_user_channel(interaction)
        if not channel:
            return
        current = channel.user_limit or 0
        new_limit = min(current + 1, 99)
        await channel.edit(user_limit=new_limit)
        await interaction.response.send_message(f"{EMOJI_CHECKMARK} User limit increased to **{new_limit}**.", ephemeral=True)

    @discord.ui.button(emoji=EMOJI_DECREASE, style=discord.ButtonStyle.secondary, custom_id="vm_decrease", row=1)
    async def decrease_limit(self, interaction: discord.Interaction, button: Button):
        channel, _ = await self.validate_user_channel(interaction)
        if not channel:
            return
        current = channel.user_limit or 0
        new_limit = max(current - 1, 0)
        await channel.edit(user_limit=new_limit)
        limit_display = "Unlimited" if new_limit == 0 else str(new_limit)
        await interaction.response.send_message(f"{EMOJI_CHECKMARK} User limit decreased to **{limit_display}**.", ephemeral=True)

    @discord.ui.button(emoji=EMOJI_INFO, style=discord.ButtonStyle.secondary, custom_id="vm_info", row=1)
    async def info_channel(self, interaction: discord.Interaction, button: Button):
        channel, owner_id = await self.validate_user_channel(interaction, allow_non_owner=True)
        if not channel:
            return
        owner = interaction.guild.get_member(owner_id)
        owner_name = owner.display_name if owner else f"ID: {owner_id}"
        limit_str = "Unlimited" if channel.user_limit == 0 else str(channel.user_limit)

        embed = discord.Embed(color=EMBED_COLOR)
        embed.set_author(name=f"Channel Information — {channel.name}", icon_url=interaction.guild.icon.url if interaction.guild.icon else None)
        embed.add_field(name="Owner", value=owner_name, inline=True)
        embed.add_field(name="Bitrate", value=f"{channel.bitrate // 1000}kbps", inline=True)
        embed.add_field(name="Connected", value=f"{len(channel.members)}/{limit_str}", inline=True)
        await interaction.response.send_message(embed=embed, ephemeral=True)

# ==========================================
# BOT CLIENT CLASS SETUP
# ==========================================
class ScythBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=discord.Intents.all(), help_command=None)

    async def setup_hook(self):
        init_db()
        self.add_view(VoiceMasterInterface())
        check_scheduled_nukes.start()

        # Connect to active public Lavalink v4 nodes
        nodes = [
            wavelink.Node(
                uri="https://lavalink.jirayu.net:443",
                password="youshallnotpass",
                inactive_player_timeout=300
            ),
            wavelink.Node(
                uri="https://lava-v4.millohost.my.id:443",
                password="https://discord.gg/mjS5J2K3ep",
                inactive_player_timeout=300
            ),
        ]
        await wavelink.Pool.connect(nodes=nodes, client=self, cache_capacity=100)

   # Launch Web Dashboard concurrently (checks both root and dashboard/ folder)
        try:
            try:
                from app import app as web_app
            except ModuleNotFoundError:
                from dashboard.app import app as web_app

            import uvicorn
            web_port = int(os.getenv("SERVER_PORT", os.getenv("PORT", 25606)))
            config = uvicorn.Config(web_app, host="0.0.0.0", port=web_port, log_level="warning")
            server = uvicorn.Server(config)
            asyncio.create_task(server.serve())
            print(f"Web Dashboard online on port {web_port}")
        except ModuleNotFoundError:
            print("[Warning] Could not find 'app.py' in root or in 'dashboard/' folder. Bot is starting without the web dashboard.")
        except Exception as e:
            print(f"[Warning] Web Dashboard error: {e}")
bot = ScythBot()

# ==========================================
# ANTI-NUKE MONITOR ENGINE
# ==========================================
async def handle_antinuke_trigger(guild: discord.Guild, action_type: discord.AuditLogAction, action_name: str):
    await asyncio.sleep(0.5)
    try:
        async for entry in guild.audit_logs(limit=1, action=action_type):
            actor = entry.user
            if not actor or actor.id == bot.user.id or actor.id == guild.owner_id:
                return

            member = guild.get_member(actor.id)
            if not member:
                return

            now = time.time()
            user_actions = antinuke_tracker[guild.id][member.id]
            user_actions.append(now)

            while user_actions and now - user_actions[0] > 10.0:
                user_actions.popleft()

            if len(user_actions) > 3:
                user_actions.clear()
                roles_to_keep = [r for r in member.roles if r.is_default()]
                try:
                    await member.edit(roles=roles_to_keep, reason=f"Anti-Nuke: Triggered limit on {action_name}")
                except discord.HTTPException:
                    pass

                try:
                    await guild.ban(member, reason=f"Anti-Nuke: Mass {action_name} (>3 in 10s)")
                    log_mod_action(guild.id, "ANTI-NUKE BAN", member.id, bot.user.id, f"Mass {action_name}")
                except discord.HTTPException:
                    pass
    except discord.Forbidden:
        pass
    except Exception as e:
        print(f"Anti-Nuke Error: {e}")

# ==========================================
# GATEWAY EVENTS
# ==========================================
@bot.event
async def on_ready():
    print(f"scyth is online as {bot.user.name} ({bot.user.id})")
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="scyth security"))

@bot.event
async def on_wavelink_node_ready(payload: wavelink.NodeReadyEventPayload):
    print(f"Lavalink Node connected: {payload.node.identifier}")

# ==========================================
# REFINED NOW PLAYING EMBED & BULLETPROOF AUTOPLAY
# ==========================================
def clean_song_title(title: str) -> str:
    """Strips messy YouTube suffixes so embeds look like clean Spotify tracks."""
    cleaned = re.sub(r'(?i)\s*[\(\[](?:official\s*(?:video|audio|music\s*video)?|lyrics?|lyric\s*video|audio|visualizer|hd|4k)[\)\]]', '', title)
    return cleaned.strip()

# ==========================================
# CLEAN ALBUM ARTWORK RESOLVER & MINIMAL EMBED
# ==========================================
async def fetch_clean_album_art(title: str, artist: str) -> Optional[str]:
    """Fetches official 1:1 square album art to eliminate 16:9 black bars."""
    try:
        clean_term = re.sub(r'\(.*?\)|\[.*?\]', '', f"{title} {artist}").strip()
        encoded = urllib.parse.quote(clean_term)
        url = f"https://itunes.apple.com/search?term={encoded}&entity=song&limit=1"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        def fetch():
            with urllib.request.urlopen(req, timeout=3) as resp:
                return json.loads(resp.read().decode())
        data = await asyncio.to_thread(fetch)
        results = data.get("results", [])
        if results and "artworkUrl100" in results[0]:
            return results[0]["artworkUrl100"].replace("100x100bb", "1000x1000bb")
    except Exception:
        pass
    return None

@bot.event
async def on_wavelink_track_start(payload: wavelink.TrackStartEventPayload):
    player: wavelink.Player = payload.player
    if not player:
        return
    track: wavelink.Playable = payload.track

    clean_title = clean_song_title(track.title)
    artist = track.author or "Unknown"

    # Fetch high-res square album artwork
    clean_art = await fetch_clean_album_art(clean_title, artist)
    final_art = clean_art or track.artwork or ""

    # 1. Update Dev Server Discord Status
    if player.guild.id == MAIN_GUILD_ID:
        status_text = f"{clean_title} • {artist}"
        if len(status_text) > 128:
            status_text = status_text[:125] + "..."
        await bot.change_presence(
            activity=discord.Activity(type=discord.ActivityType.listening, name=status_text)
        )

        with sqlite3.connect(DB_NAME) as conn:
            conn.cursor().execute("""
                INSERT OR REPLACE INTO active_playback (guild_id, title, artist, uri, artwork, duration, started_at, is_playing)
                VALUES (?, ?, ?, ?, ?, ?, ?, 1)
            """, (player.guild.id, clean_title, artist, track.uri, final_art, track.length // 1000, time.time()))
            conn.commit()

    # 2. Clean, Minimal Now Playing Embed (Reverted to the clean layout)
    channel = getattr(player, "home_channel", None)
    if channel:
        dur_str = format_duration(track.length // 1000)

        embed = discord.Embed(
            title=f"{EMOJI_DISC} Now Playing",
            description=f"[{clean_title}]({track.uri})",
            color=EMBED_COLOR
        )
        embed.add_field(name="Duration", value=dur_str, inline=True)
        embed.add_field(name="Artist", value=artist, inline=True)

        if final_art:
            embed.set_thumbnail(url=final_art)

        embed.set_footer(text="scyth • music", icon_url=bot.user.display_avatar.url)
        await channel.send(embed=embed)

@bot.event
async def on_wavelink_track_exception(payload: wavelink.TrackExceptionEventPayload):
    """Fails over to clean audio streams, rejecting lyric videos and spam edits."""
    player: wavelink.Player = payload.player
    track: wavelink.Playable = payload.track
    if not player:
        return

    clean_name = clean_song_title(track.title)
    search_query = f"{clean_name} {track.author}".strip()

    try:
        results = await wavelink.Playable.search(search_query, source=wavelink.TrackSource.SoundCloud)
        if results:
            for cand in results[:5]:
                if not any(x in cand.title.lower() for x in ["lyric", "1 hour", "slowed", "sped up", "reverb"]):
                    await player.play(cand)
                    return
    except Exception:
        pass

    if player.queue:
        await player.play(player.queue.get())

@bot.event
async def on_wavelink_inactive_player(player: wavelink.Player):
    channel = getattr(player, "home_channel", None)
    if channel:
        embed = discord.Embed(
            description=f"{EMOJI_CLOCK} Left the voice channel — no music has been played in the last 5 minutes.",
            color=EMBED_COLOR
        )
        embed.set_footer(text="scyth • music", icon_url=bot.user.display_avatar.url)
        await channel.send(embed=embed)

    if player.guild.id == MAIN_GUILD_ID:
        with sqlite3.connect(DB_NAME) as conn:
            conn.cursor().execute("UPDATE active_playback SET is_playing = 0 WHERE guild_id = ?", (player.guild.id,))
            conn.commit()
        await bot.change_presence(
            activity=discord.Activity(type=discord.ActivityType.watching, name="scyth security")
        )
    await player.disconnect()

@bot.event
async def on_guild_channel_create(channel: discord.abc.GuildChannel):
    await handle_antinuke_trigger(channel.guild, discord.AuditLogAction.channel_create, "Channel Create")

@bot.event
async def on_guild_channel_delete(channel: discord.abc.GuildChannel):
    await handle_antinuke_trigger(channel.guild, discord.AuditLogAction.channel_delete, "Channel Delete")

@bot.event
async def on_guild_role_delete(role: discord.Role):
    await handle_antinuke_trigger(role.guild, discord.AuditLogAction.role_delete, "Role Delete")

@bot.event
async def on_member_ban(guild: discord.Guild, user: Union[discord.User, discord.Member]):
    await handle_antinuke_trigger(guild, discord.AuditLogAction.ban, "Member Ban")

@bot.event
async def on_member_unban(guild: discord.Guild, user: discord.User):
    """Automatically rebans anyone in the hardban blacklist if someone manually unbans them."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT reason FROM hardbans WHERE guild_id = ? AND user_id = ?", (guild.id, user.id))
        row = cursor.fetchone()

    if row:
        reason = row[0]
        await asyncio.sleep(1)
        try:
            await guild.ban(user, reason=f"Scyth Hardban Enforcement: Auto-rebanned ({reason})")
            log_mod_action(guild.id, "HARDBAN ENFORCE", user.id, bot.user.id, "Manual unban intercepted")
        except discord.HTTPException:
            pass

@bot.event
async def on_member_join(member: discord.Member):
    guild = member.guild
    now = time.time()
    join_times = raid_tracker[guild.id]
    join_times.append(now)

    while join_times and now - join_times[0] > 10.0:
        join_times.popleft()

    if len(join_times) > 5:
        try:
            await member.kick(reason="Anti-Raid: Join rate threshold exceeded (>5 in 10s)")
            log_mod_action(guild.id, "ANTI-RAID KICK", member.id, bot.user.id, "Mass Join Raid Trigger")
        except discord.Forbidden:
            pass

@bot.event
async def on_message_delete(message: discord.Message):
    if message.author.bot or not message.guild:
        return
    sniped_messages[message.channel.id] = {
        "content": message.content,
        "author": message.author,
        "timestamp": message.created_at,
        "attachment": message.attachments[0].url if message.attachments else None
    }

@bot.event
async def on_message_edit(before: discord.Message, after: discord.Message):
    if before.author.bot or not before.guild or before.content == after.content:
        return
    edited_messages[before.channel.id] = {
        "before": before.content,
        "after": after.content,
        "author": before.author,
        "timestamp": before.created_at,
    }

@bot.event
async def on_message(message: discord.Message):
    if message.author.bot or not message.guild:
        return

    # --- Media-Only Enforcement ---
    if not message.author.guild_permissions.administrator:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM media_only_channels WHERE guild_id = ? AND channel_id = ?",
                           (message.guild.id, message.channel.id))
            is_media_only = cursor.fetchone()

        if is_media_only:
            has_media = bool(message.attachments) or any(
                ext in message.content.lower() for ext in ["http://", "https://", "tenor.com", "giphy.com"]
            )
            if not has_media:
                try:
                    await message.delete()
                    return
                except discord.Forbidden:
                    pass

    # --- AFK Notification System ---
    if remove_afk_status(message.author.id, message.guild.id):
        await message.channel.send(
            f"{EMOJI_BELL} Welcome back {message.author.mention}, your AFK status has been removed.",
            delete_after=6
        )

    if message.mentions:
        for user in message.mentions:
            if user.id == message.author.id:
                continue
            afk_data = get_afk_status(user.id, message.guild.id)
            if afk_data:
                reason, afk_timestamp = afk_data
                time_ago = f"<t:{int(afk_timestamp)}:R>"
                embed = discord.Embed(
                    description=f"{EMOJI_BELL} **{user.display_name}** is currently AFK: {reason} — {time_ago}",
                    color=EMBED_COLOR
                )
                await message.channel.send(embed=embed, delete_after=8)

    # --- Autoresponders ---
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT response FROM autoresponders WHERE guild_id = ? AND trigger = ?",
                       (message.guild.id, message.content.lower().strip()))
        ar_match = cursor.fetchone()
    if ar_match:
        await message.channel.send(ar_match[0])

    # --- Anti-Invite Filter ---
    if INVITE_REGEX.search(message.content):
        if not message.author.guild_permissions.administrator:
            try:
                await message.delete()
                await message.channel.send(f"{EMOJI_CROSS} {message.author.mention}, invite links are not permitted here!", delete_after=5)
                return
            except discord.Forbidden:
                pass

    # --- Anti-Spam Filter ---
    if not message.author.guild_permissions.administrator:
        now = time.time()
        user_msgs = spam_tracker[message.author.id]
        user_msgs.append(now)

        while user_msgs and now - user_msgs[0] > 3.0:
            user_msgs.popleft()

        if len(user_msgs) > 5:
            user_msgs.clear()
            try:
                await message.author.timeout(datetime.timedelta(minutes=5), reason="Anti-Spam: Message flooding")
                await message.channel.send(f"{EMOJI_CLOCK} {message.author.mention} has been timed out for 5 minutes for spamming.", delete_after=10)
                log_mod_action(message.guild.id, "ANTI-SPAM TIMEOUT", message.author.id, bot.user.id, "Message flooding")
                return
            except (discord.Forbidden, discord.HTTPException):
                pass

    await bot.process_commands(message)

@bot.event
async def on_voice_state_update(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
    guild = member.guild
    config = get_vm_config(guild.id)

    if config:
        category_id, jtc_id, interface_id = config

        if after.channel and after.channel.id == jtc_id:
            category = guild.get_channel(category_id)
            if category:
                new_channel = await guild.create_voice_channel(
                    name=f"{member.display_name}'s channel",
                    category=category,
                    user_limit=0
                )
                await new_channel.set_permissions(member, connect=True, speak=True, stream=True)
                await member.move_to(new_channel)
                add_temp_channel(new_channel.id, guild.id, member.id)

                interface_channel = guild.get_channel(interface_id)
                if interface_channel:
                    try:
                        await interface_channel.send(
                            f"{member.mention}, your voice channel has been created! Use the controls above to configure it.",
                            delete_after=7
                        )
                    except discord.HTTPException:
                        pass

        if before.channel and before.channel.id != jtc_id:
            owner_id = get_temp_channel_owner(before.channel.id)
            if owner_id and len(before.channel.members) == 0:
                remove_temp_channel(before.channel.id)
                try:
                    await before.channel.delete(reason="Temporary Voice Channel Empty")
                except discord.NotFound:
                    pass

# ==========================================
# SCHEDULED AUTO-NUKE ENGINE
# ==========================================
@tasks.loop(seconds=30)
async def check_scheduled_nukes():
    now = time.time()
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT channel_id, guild_id, wipe_interval_seconds FROM scheduled_nukes WHERE next_wipe_timestamp <= ?", (now,))
        due_channels = cursor.fetchall()

        for channel_id, guild_id, interval in due_channels:
            guild = bot.get_guild(guild_id)
            if not guild:
                continue
            channel = guild.get_channel(channel_id)
            if not channel:
                cursor.execute("DELETE FROM scheduled_nukes WHERE channel_id = ?", (channel_id,))
                conn.commit()
                continue

            try:
                pos = channel.position
                new_channel = await channel.clone(reason="Scheduled Auto-Nuke Wiped Channel")
                await channel.delete(reason="Scheduled Auto-Nuke Wiped Channel")
                await new_channel.edit(position=pos)

                embed = discord.Embed(
                    title=f"{EMOJI_CLOCK} Scheduled Auto-Nuke",
                    description=f"This channel's chat history has been automatically wiped on its timer ({interval // 60} minutes).",
                    color=EMBED_COLOR
                )
                embed.set_image(url="https://media.giphy.com/media/oe33xf3B50fsc/giphy.gif")
                embed.set_footer(text="scyth • auto-nuke")
                await new_channel.send(embed=embed)

                next_time = time.time() + interval
                cursor.execute("UPDATE scheduled_nukes SET next_wipe_timestamp = ? WHERE channel_id = ?", (next_time, channel_id))
                conn.commit()
            except Exception as e:
                print(f"Error executing auto-nuke on channel {channel_id}: {e}")

@check_scheduled_nukes.before_loop
async def before_check_scheduled_nukes():
    await bot.wait_until_ready()

# ==========================================
# MUSIC COMMANDS
# ==========================================

# ==========================================
# LAVALINK MUSIC ENGINE (CLEAN CONNECTION & EMBEDS)
# ==========================================
@bot.command(name="play", aliases=["p"])
async def play(ctx: commands.Context, *, query: Optional[str] = None):
    """Streams music from Spotify, YouTube, or SoundCloud with instant embed feedback."""
    if not query:
        return await ctx.send(embed=get_syntax_embed("play"))

    if not ctx.author.voice or not ctx.author.voice.channel:
        embed = discord.Embed(description=f"{EMOJI_CROSS} You must be in a voice channel to play music.", color=EMBED_COLOR)
        return await ctx.send(embed=embed)

    status_msg = await ctx.send(embed=discord.Embed(
        description=f"{EMOJI_CLOCK} Searching for **{query}**...",
        color=EMBED_COLOR
    ))

    # 1. Voice Connection: Use existing player if already in VC
    player: wavelink.Player = ctx.voice_client
    if not player:
        try:
            player = await ctx.author.voice.channel.connect(cls=wavelink.Player, self_deaf=True)
        except Exception:
            embed = discord.Embed(description=f"{EMOJI_CROSS} Could not join your voice channel. Check bot permissions.", color=EMBED_COLOR)
            return await status_msg.edit(embed=embed)
    elif player.channel != ctx.author.voice.channel:
        await player.move_to(ctx.author.voice.channel)

    player.home_channel = ctx.channel

    # 2. Search Primary (Spotify / YouTube Music) with SoundCloud fallback
    tracks = None
    try:
        tracks = await wavelink.Playable.search(query)
    except Exception:
        tracks = None

    if not tracks:
        try:
            tracks = await wavelink.Playable.search(query, source=wavelink.TrackSource.SoundCloud)
        except Exception:
            tracks = None

    if not tracks:
        embed = discord.Embed(description=f"{EMOJI_CROSS} Could not find that track on any platform.", color=EMBED_COLOR)
        return await status_msg.edit(embed=embed)

    # 3. Handle Playlists
    if isinstance(tracks, wavelink.Playlist):
        added: int = await player.queue.put_wait(tracks)
        embed = discord.Embed(
            title=f"{EMOJI_CHECKMARK} Queued Playlist",
            description=f"Loaded **{added}** tracks from **{tracks.name}**.",
            color=EMBED_COLOR
        )
        if tracks.artwork:
            embed.set_thumbnail(url=tracks.artwork)
        embed.set_footer(text="scyth • music", icon_url=bot.user.display_avatar.url)
        await status_msg.edit(embed=embed)
        if not player.playing:
            await player.play(player.queue.get(), volume=50)
        return

    # 4. Handle Single Tracks
    track: wavelink.Playable = tracks[0]

    if player.playing:
        await player.queue.put_wait(track)
        embed = discord.Embed(
            title=f"{EMOJI_CHECKMARK} Added to Queue",
            description=f"[{track.title}]({track.uri})",
            color=EMBED_COLOR
        )
        if track.artwork:
            embed.set_thumbnail(url=track.artwork)
        embed.add_field(name="Duration", value=format_duration(track.length // 1000), inline=True)
        embed.add_field(name="Position in Queue", value=f"#{len(player.queue)}", inline=True)
        embed.set_footer(text="scyth • music", icon_url=bot.user.display_avatar.url)
        await status_msg.edit(embed=embed)
    else:
        # Nothing is playing -> Start track and immediately show the Now Playing card!
        await player.play(track, volume=50)
        embed = discord.Embed(
            title=f"{EMOJI_DISC} Now Playing",
            description=f"[{track.title}]({track.uri})",
            color=EMBED_COLOR
        )
        if track.artwork:
            embed.set_thumbnail(url=track.artwork)
        embed.add_field(name="Duration", value=format_duration(track.length // 1000), inline=True)
        embed.add_field(name="Artist", value=track.author or "Unknown", inline=True)
        embed.set_footer(text="scyth • music", icon_url=bot.user.display_avatar.url)
        await status_msg.edit(embed=embed)

@bot.command(name="playnext", aliases=["pn"])
async def playnext(ctx: commands.Context, *, query: Optional[str] = None):
    """Inserts a track straight to the very front of the audio queue."""
    if not query:
        return await ctx.send(embed=get_syntax_embed("playnext"))

    if not ctx.author.voice or not ctx.author.voice.channel:
        embed = discord.Embed(description=f"{EMOJI_CROSS} You must be in a voice channel to play music.", color=EMBED_COLOR)
        return await ctx.send(embed=embed)

    status_msg = await ctx.send(embed=discord.Embed(
        description=f"{EMOJI_CLOCK} Searching for **{query}**...",
        color=EMBED_COLOR
    ))

    player: wavelink.Player = ctx.voice_client
    if not player:
        try:
            player = await ctx.author.voice.channel.connect(cls=wavelink.Player, self_deaf=True)
        except Exception:
            embed = discord.Embed(description=f"{EMOJI_CROSS} Could not join voice.", color=EMBED_COLOR)
            return await status_msg.edit(embed=embed)

    player.home_channel = ctx.channel

    tracks = None
    try:
        tracks = await wavelink.Playable.search(query)
    except Exception:
        tracks = None

    if not tracks:
        try:
            tracks = await wavelink.Playable.search(query, source=wavelink.TrackSource.SoundCloud)
        except Exception:
            tracks = None

    if not tracks:
        embed = discord.Embed(description=f"{EMOJI_CROSS} Could not find that track.", color=EMBED_COLOR)
        return await status_msg.edit(embed=embed)

    track: wavelink.Playable = tracks[0]

    if not player.playing:
        await player.play(track, volume=50)
        embed = discord.Embed(
            title=f"{EMOJI_DISC} Now Playing",
            description=f"[{track.title}]({track.uri})",
            color=EMBED_COLOR
        )
        if track.artwork:
            embed.set_thumbnail(url=track.artwork)
        embed.add_field(name="Duration", value=format_duration(track.length // 1000), inline=True)
        embed.add_field(name="Artist", value=track.author or "Unknown", inline=True)
        embed.set_footer(text="scyth • music", icon_url=bot.user.display_avatar.url)
        await status_msg.edit(embed=embed)
    else:
        player.queue.put_at(0, track)
        embed = discord.Embed(
            title=f"{EMOJI_CHECKMARK} Added Up Next",
            description=f"[{track.title}]({track.uri})",
            color=EMBED_COLOR
        )
        if track.artwork:
            embed.set_thumbnail(url=track.artwork)
        embed.set_footer(text="scyth • music", icon_url=bot.user.display_avatar.url)
        await status_msg.edit(embed=embed)

@bot.command(name="skip", aliases=["sk"])
async def skip(ctx: commands.Context):
    """Skips the currently playing track."""
    player: wavelink.Player = ctx.voice_client
    if not player or not player.playing:
        embed = discord.Embed(description=f"{EMOJI_CROSS} No music is currently playing.", color=EMBED_COLOR)
        return await ctx.send(embed=embed)

    try:
        await player.skip(force=True)
        embed = discord.Embed(description=f"{EMOJI_CHECKMARK} Skipped current track.", color=EMBED_COLOR)
        await ctx.send(embed=embed)
    except wavelink.exceptions.LavalinkException:
        embed = discord.Embed(description=f"{EMOJI_CROSS} Could not skip track — player was not found on the audio node.", color=EMBED_COLOR)
        await ctx.send(embed=embed)

@bot.command(name="pause")
async def pause(ctx: commands.Context):
    """Pauses the current track."""
    player: wavelink.Player = ctx.voice_client
    if not player or not player.playing:
        embed = discord.Embed(description=f"{EMOJI_CROSS} No music is currently playing.", color=EMBED_COLOR)
        return await ctx.send(embed=embed)

    try:
        await player.pause(True)
        embed = discord.Embed(description=f"{EMOJI_CHECKMARK} Paused playback. Use `!resume` to continue.", color=EMBED_COLOR)
        await ctx.send(embed=embed)
    except wavelink.exceptions.LavalinkException:
        embed = discord.Embed(description=f"{EMOJI_CROSS} Could not pause track.", color=EMBED_COLOR)
        await ctx.send(embed=embed)

@bot.command(name="resume", aliases=["unpause"])
async def resume(ctx: commands.Context):
    """Resumes playback if paused."""
    player: wavelink.Player = ctx.voice_client
    if not player or not player.paused:
        embed = discord.Embed(description=f"{EMOJI_CROSS} Music is not currently paused.", color=EMBED_COLOR)
        return await ctx.send(embed=embed)

    try:
        await player.pause(False)
        embed = discord.Embed(description=f"{EMOJI_CHECKMARK} Resumed playback.", color=EMBED_COLOR)
        await ctx.send(embed=embed)
    except wavelink.exceptions.LavalinkException:
        embed = discord.Embed(description=f"{EMOJI_CROSS} Could not resume track.", color=EMBED_COLOR)
        await ctx.send(embed=embed)

@bot.command(name="stop", aliases=["disconnect", "dc"])
async def stop(ctx: commands.Context):
    """Stops playback, clears queue, and disconnects the bot."""
    player: wavelink.Player = ctx.voice_client
    if not player:
        embed = discord.Embed(description=f"{EMOJI_CROSS} Not connected to any voice channel.", color=EMBED_COLOR)
        return await ctx.send(embed=embed)

    player.queue.clear()
    await player.disconnect()

    if ctx.guild.id == MAIN_GUILD_ID:
        await bot.change_presence(
            activity=discord.Activity(type=discord.ActivityType.watching, name="scyth security")
        )

    embed = discord.Embed(description=f"{EMOJI_CHECKMARK} Disconnected and cleared queue.", color=EMBED_COLOR)
    await ctx.send(embed=embed)

@bot.command(name="queue", aliases=["q"])
async def queue_command(ctx: commands.Context):
    """Displays the current music queue."""
    player: wavelink.Player = ctx.voice_client
    if not player or (not player.current and not player.queue):
        embed = discord.Embed(description=f"{EMOJI_CROSS} The music queue is currently empty.", color=EMBED_COLOR)
        return await ctx.send(embed=embed)

    embed = discord.Embed(title=f"{EMOJI_DISC} Server Music Queue", color=EMBED_COLOR)
    if player.current:
        embed.add_field(
            name="Now Playing",
            value=f"[{player.current.title}]({player.current.uri}) | `{format_duration(player.current.length // 1000)}`",
            inline=False
        )

    if player.queue:
        queue_list = []
        for idx, trk in enumerate(list(player.queue)[:10], start=1):
            queue_list.append(f"`{idx}.` [{trk.title}]({trk.uri}) — `{format_duration(trk.length // 1000)}`")
        embed.add_field(name="Upcoming", value="\n".join(queue_list), inline=False)
        if len(player.queue) > 10:
            embed.set_footer(text=f"Plus {len(player.queue) - 10} more songs in queue • scyth")
    else:
        embed.add_field(name="Upcoming", value="No more tracks in queue.", inline=False)

    await ctx.send(embed=embed)

@bot.command(name="clearqueue", aliases=["clearq", "cq"])
async def clearqueue(ctx: commands.Context):
    """Flushes all queued songs."""
    player: wavelink.Player = ctx.voice_client
    if not player or not player.queue:
        embed = discord.Embed(description=f"{EMOJI_CROSS} The queue is already empty.", color=EMBED_COLOR)
        return await ctx.send(embed=embed)

    count = len(player.queue)
    player.queue.clear()
    embed = discord.Embed(description=f"{EMOJI_TRASH} Removed **{count}** tracks from the queue.", color=EMBED_COLOR)
    await ctx.send(embed=embed)

@bot.command(name="shuffle", aliases=["sh"])
async def shuffle(ctx: commands.Context):
    """Shuffles the queued songs."""
    player: wavelink.Player = ctx.voice_client
    if not player or len(player.queue) < 2:
        embed = discord.Embed(description=f"{EMOJI_CROSS} Need at least 2 tracks in queue to shuffle.", color=EMBED_COLOR)
        return await ctx.send(embed=embed)

    player.queue.shuffle()
    embed = discord.Embed(description=f"{EMOJI_CHECKMARK} Shuffled **{len(player.queue)}** tracks in queue.", color=EMBED_COLOR)
    await ctx.send(embed=embed)

@bot.command(name="volume", aliases=["vol", "v"])
async def volume(ctx: commands.Context, level: Optional[int] = None):
    """Adjusts music volume percentage (1-100%)."""
    player: wavelink.Player = ctx.voice_client
    if not player:
        embed = discord.Embed(description=f"{EMOJI_SPEAKER} Not connected to voice.", color=EMBED_COLOR)
        return await ctx.send(embed=embed)

    if level is None or not (1 <= level <= 100):
        return await ctx.send(embed=get_syntax_embed("volume"))

    await player.set_volume(level)
    embed = discord.Embed(description=f"{EMOJI_CHECKMARK} Playback volume set to **{level}%**.", color=EMBED_COLOR)
    await ctx.send(embed=embed)

@bot.command(name="autoplay", aliases=["ap"])
async def autoplay(ctx: commands.Context):
    """Toggles intelligent recommendation autoplay."""
    player: wavelink.Player = ctx.voice_client
    if not player:
        embed = discord.Embed(description=f"{EMOJI_CROSS} Not connected to voice.", color=EMBED_COLOR)
        return await ctx.send(embed=embed)

    if player.autoplay == wavelink.AutoPlayMode.enabled:
        player.autoplay = wavelink.AutoPlayMode.disabled
        state = "disabled"
    else:
        player.autoplay = wavelink.AutoPlayMode.enabled
        state = "enabled"

    embed = discord.Embed(description=f"{EMOJI_CHECKMARK} Autoplay has been **{state}**.", color=EMBED_COLOR)
    await ctx.send(embed=embed)

# ==========================================
# AFK COMMAND
# ==========================================
@bot.command(name="afk", aliases=["away"])
async def afk_command(ctx: commands.Context, *, reason: str = "AFK"):
    """Sets your global status to AFK."""
    set_afk_status(ctx.author.id, ctx.guild.id, reason)
    embed = discord.Embed(
        description=f"{EMOJI_BELL} {ctx.author.mention}: You're now AFK with status: **{reason}**",
        color=EMBED_COLOR
    )
    await ctx.send(embed=embed)

# ==========================================
# AUTO-NUKE GROUP COMMANDS
# ==========================================
@bot.group(name="autonuke", aliases=["an"], invoke_without_command=True)
@commands.has_permissions(manage_channels=True)
async def autonuke(ctx: commands.Context):
    """Manage automatic channel nukes/wipes."""
    await ctx.send(embed=get_syntax_embed("autonuke"))

@autonuke.command(name="set", aliases=["s"])
@commands.has_permissions(manage_channels=True)
async def autonuke_set(ctx: commands.Context, minutes: Optional[int] = None):
    """Sets an automatic nuke timer for the current channel."""
    if minutes is None or minutes < 1 or minutes > 10080:
        return await ctx.send(embed=get_syntax_embed("autonuke"))

    interval_seconds = minutes * 60
    next_timestamp = time.time() + interval_seconds

    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO scheduled_nukes (channel_id, guild_id, wipe_interval_seconds, next_wipe_timestamp)
            VALUES (?, ?, ?, ?)
        """, (ctx.channel.id, ctx.guild.id, interval_seconds, next_timestamp))
        conn.commit()

    await ctx.send(f"{EMOJI_CHECKMARK} Auto-nuke enabled for this channel! It will automatically wipe every **{minutes} minute(s)**.")

@autonuke.command(name="remove", aliases=["rm", "r", "delete", "del"])
@commands.has_permissions(manage_channels=True)
async def autonuke_remove(ctx: commands.Context):
    """Disables auto-nuke for the current channel."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM scheduled_nukes WHERE channel_id = ?", (ctx.channel.id,))
        deleted = cursor.rowcount
        conn.commit()

    if deleted > 0:
        await ctx.send(f"{EMOJI_CHECKMARK} Auto-nuke has been disabled for this channel.")
    else:
        embed = discord.Embed(description=f"{EMOJI_CROSS} This channel does not have an active auto-nuke timer.", color=EMBED_COLOR)
        await ctx.send(embed=embed)

# ==========================================
# VOICEMASTER SETUP COMMAND
# ==========================================
@bot.command(name="voicemaster", aliases=["vm"])
@commands.has_permissions(administrator=True)
async def voicemaster_command(ctx: commands.Context, action: Optional[str] = None):
    """Configures the VoiceMaster category, voice join channel, and interface panel."""
    if action != "setup":
        return await ctx.send(embed=get_syntax_embed("voicemaster"))

    guild = ctx.guild
    category = await guild.create_category(name="Voice Channels")

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(
            view_channel=True,
            send_messages=False,
            read_message_history=True
        ),
        guild.me: discord.PermissionOverwrite(
            view_channel=True,
            send_messages=True,
            embed_links=True,
            manage_messages=True
        )
    }
    interface_channel = await guild.create_text_channel(
        name="・interface",
        category=category,
        overwrites=overwrites
    )

    jtc_channel = await guild.create_voice_channel(
        name="Join to Create",
        category=category,
        user_limit=0
    )

    save_vm_config(guild.id, category.id, jtc_channel.id, interface_channel.id)

    embed = discord.Embed(
        title="VoiceMaster Interface",
        description=(
            "Click the buttons below to control your temporary voice channel.\n\n"
            f"> {EMOJI_LOCK} — Lock your voice channel\n"
            f"> {EMOJI_UNLOCK} — Unlock your voice channel\n"
            f"> {EMOJI_GHOST} — Hide your voice channel\n"
            f"> {EMOJI_UNGHOST} — Reveal your voice channel\n"
            f"> {EMOJI_CLAIM} — Claim inactive voice channel\n"
            f"> {EMOJI_DISCONNECT} — Disconnect a user\n"
            f"> {EMOJI_ACTIVITY} — Launch an activity\n"
            f"> {EMOJI_INCREASE} — Increase member limit\n"
            f"> {EMOJI_DECREASE} — Decrease member limit\n"
            f"> {EMOJI_INFO} — View channel information"
        ),
        color=EMBED_COLOR
    )
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
    embed.set_footer(text="scyth • voicemaster")

    view = VoiceMasterInterface()
    await interface_channel.send(embed=embed, view=view)
    await ctx.send(f"{EMOJI_CHECKMARK} VoiceMaster system successfully configured in {interface_channel.mention}!")

# ==========================================
# ADVANCED MODERATION SUITE
# ==========================================
async def get_or_create_jail_setup(guild: discord.Guild):
    jail_role = discord.utils.get(guild.roles, name="Jailed")
    if not jail_role:
        jail_role = await guild.create_role(name="Jailed", color=discord.Color.dark_grey(), reason="Scyth Jail System")
        for channel in guild.channels:
            try:
                await channel.set_permissions(jail_role, view_channel=False, send_messages=False)
            except discord.Forbidden:
                pass

    jail_channel = discord.utils.get(guild.text_channels, name="jail")
    if not jail_channel:
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            jail_role: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }
        jail_channel = await guild.create_text_channel(name="jail", overwrites=overwrites, reason="Scyth Jail System")

    return jail_role, jail_channel

@bot.command(name="jail")
@has_permission_or_fake("moderate_members")
async def jail(ctx: commands.Context, member: discord.Member, *, reason: str = "No reason provided"):
    """Isolates a member to the jail channel and preserves their existing roles in SQLite."""
    if member.top_role >= ctx.author.top_role and ctx.author.id != ctx.guild.owner_id:
        embed = discord.Embed(description=f"{EMOJI_CROSS} You cannot jail someone with an equal or higher role than you.", color=EMBED_COLOR)
        return await ctx.send(embed=embed)

    jail_role, jail_channel = await get_or_create_jail_setup(ctx.guild)
    if jail_role in member.roles:
        embed = discord.Embed(description=f"{EMOJI_CROSS} **{member}** is already jailed.", color=EMBED_COLOR)
        return await ctx.send(embed=embed)

    saved_roles = [r.id for r in member.roles if not r.is_default() and not r.managed]
    saved_roles_str = ",".join(map(str, saved_roles))

    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO jailed_users (guild_id, user_id, role_ids) VALUES (?, ?, ?)",
                       (ctx.guild.id, member.id, saved_roles_str))
        conn.commit()

    try:
        await member.edit(roles=[jail_role], reason=f"Jailed by {ctx.author}: {reason}")
    except discord.Forbidden:
        embed = discord.Embed(description=f"{EMOJI_CROSS} I lack permissions to modify roles for **{member}**.", color=EMBED_COLOR)
        return await ctx.send(embed=embed)

    log_mod_action(ctx.guild.id, "JAIL", member.id, ctx.author.id, reason)
    embed = discord.Embed(description=f"{EMOJI_HAMMER} Jailed **{member}** in {jail_channel.mention} | Reason: {reason}", color=EMBED_COLOR)
    await ctx.send(embed=embed)

@bot.command(name="unjail")
@has_permission_or_fake("moderate_members")
async def unjail(ctx: commands.Context, member: discord.Member):
    """Restores all original roles to a jailed member."""
    jail_role, _ = await get_or_create_jail_setup(ctx.guild)

    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT role_ids FROM jailed_users WHERE guild_id = ? AND user_id = ?", (ctx.guild.id, member.id))
        row = cursor.fetchone()
        cursor.execute("DELETE FROM jailed_users WHERE guild_id = ? AND user_id = ?", (ctx.guild.id, member.id))
        conn.commit()

    if not row:
        embed = discord.Embed(description=f"{EMOJI_CROSS} **{member}** has no saved jail records.", color=EMBED_COLOR)
        return await ctx.send(embed=embed)

    role_ids = [int(rid) for rid in row[0].split(",") if rid]
    restored_roles = [ctx.guild.get_role(rid) for rid in role_ids if ctx.guild.get_role(rid)]

    try:
        await member.edit(roles=restored_roles, reason=f"Unjailed by {ctx.author}")
    except discord.Forbidden:
        embed = discord.Embed(description=f"{EMOJI_CROSS} Lacking permissions to restore roles to **{member}**.", color=EMBED_COLOR)
        return await ctx.send(embed=embed)

    log_mod_action(ctx.guild.id, "UNJAIL", member.id, ctx.author.id, "Unjailed")
    embed = discord.Embed(description=f"{EMOJI_CHECKMARK} Successfully unjailed **{member}** and restored **{len(restored_roles)}** role(s).", color=EMBED_COLOR)
    await ctx.send(embed=embed)

@bot.command(name="strip")
@has_permission_or_fake("manage_roles")
async def strip(ctx: commands.Context, member: discord.Member, *, reason: str = "Roles stripped"):
    """Strips all custom roles from a user and saves them in SQLite for quick restoration."""
    if member.top_role >= ctx.author.top_role and ctx.author.id != ctx.guild.owner_id:
        embed = discord.Embed(description=f"{EMOJI_CROSS} You cannot strip roles from someone with an equal or higher role.", color=EMBED_COLOR)
        return await ctx.send(embed=embed)

    saved_roles = [r.id for r in member.roles if not r.is_default() and not r.managed]
    if not saved_roles:
        embed = discord.Embed(description=f"{EMOJI_CROSS} **{member}** has no custom roles to strip.", color=EMBED_COLOR)
        return await ctx.send(embed=embed)

    saved_roles_str = ",".join(map(str, saved_roles))
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO stripped_users (guild_id, user_id, role_ids) VALUES (?, ?, ?)",
                       (ctx.guild.id, member.id, saved_roles_str))
        conn.commit()

    roles_to_keep = [r for r in member.roles if r.is_default() or r.managed]
    await member.edit(roles=roles_to_keep, reason=f"Roles stripped by {ctx.author}: {reason}")
    log_mod_action(ctx.guild.id, "STRIP", member.id, ctx.author.id, reason)
    embed = discord.Embed(description=f"{EMOJI_TRASH} Stripped **{len(saved_roles)}** roles from **{member}**. Use `!restore` to return them.", color=EMBED_COLOR)
    await ctx.send(embed=embed)

@bot.command(name="restore")
@has_permission_or_fake("manage_roles")
async def restore(ctx: commands.Context, member: discord.Member):
    """Restores previously stripped roles to a member."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT role_ids FROM stripped_users WHERE guild_id = ? AND user_id = ?", (ctx.guild.id, member.id))
        row = cursor.fetchone()
        cursor.execute("DELETE FROM stripped_users WHERE guild_id = ? AND user_id = ?", (ctx.guild.id, member.id))
        conn.commit()

    if not row:
        embed = discord.Embed(description=f"{EMOJI_CROSS} No stripped role records found for **{member}**.", color=EMBED_COLOR)
        return await ctx.send(embed=embed)

    role_ids = [int(rid) for rid in row[0].split(",") if rid]
    restored_roles = [ctx.guild.get_role(rid) for rid in role_ids if ctx.guild.get_role(rid)]
    new_roles = list(set(member.roles + restored_roles))

    await member.edit(roles=new_roles, reason=f"Roles restored by {ctx.author}")
    embed = discord.Embed(description=f"{EMOJI_CHECKMARK} Restored **{len(restored_roles)}** role(s) to **{member}**.", color=EMBED_COLOR)
    await ctx.send(embed=embed)

@bot.command(name="hardban")
@has_permission_or_fake("ban_members")
async def hardban(ctx: commands.Context, user_id: int, *, reason: str = "No reason provided"):
    """Bans a user and adds them to a persistent SQLite blacklist that auto-rebans them if unbanned."""
    user = await bot.fetch_user(user_id)
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO hardbans (guild_id, user_id, reason) VALUES (?, ?, ?)",
                       (ctx.guild.id, user.id, reason))
        conn.commit()

    await ctx.guild.ban(user, reason=f"Hardban by {ctx.author}: {reason}")
    log_mod_action(ctx.guild.id, "HARDBAN", user.id, ctx.author.id, reason)
    embed = discord.Embed(description=f"{EMOJI_HAMMER} Permanently hardbanned **{user}** (Auto-reban active) | Reason: {reason}", color=EMBED_COLOR)
    await ctx.send(embed=embed)

@bot.command(name="role", aliases=["r"])
@has_permission_or_fake("manage_roles")
async def role(ctx: commands.Context, member: discord.Member, *, role: discord.Role):
    """Toggles a role on or off for a member."""
    if role >= ctx.author.top_role and ctx.author.id != ctx.guild.owner_id:
        embed = discord.Embed(description=f"{EMOJI_CROSS} You cannot manage a role equal or higher than your top role.", color=EMBED_COLOR)
        return await ctx.send(embed=embed)
    if role >= ctx.guild.me.top_role:
        embed = discord.Embed(description=f"{EMOJI_CROSS} I cannot manage this role as it is above my top role.", color=EMBED_COLOR)
        return await ctx.send(embed=embed)

    if role in member.roles:
        await member.remove_roles(role, reason=f"Toggled by {ctx.author}")
        embed = discord.Embed(description=f"{EMOJI_CHECKMARK} Removed {role.mention} from **{member}**.", color=EMBED_COLOR)
    else:
        await member.add_roles(role, reason=f"Toggled by {ctx.author}")
        embed = discord.Embed(description=f"{EMOJI_CHECKMARK} Added {role.mention} to **{member}**.", color=EMBED_COLOR)
    await ctx.send(embed=embed)

@bot.command(name="ban", aliases=["b"])
@has_permission_or_fake("ban_members")
async def ban(ctx: commands.Context, member: discord.Member, *, reason: str = "No reason provided"):
    """Bans a member from the server."""
    if member.top_role >= ctx.author.top_role and ctx.author.id != ctx.guild.owner_id:
        embed = discord.Embed(description=f"{EMOJI_CROSS} You cannot ban someone with an equal or higher role than you.", color=EMBED_COLOR)
        return await ctx.send(embed=embed)

    await member.ban(reason=reason)
    log_mod_action(ctx.guild.id, "BAN", member.id, ctx.author.id, reason)
    await ctx.send(f"{EMOJI_HAMMER} Successfully banned **{member}** | Reason: {reason}")

@bot.command(name="unban", aliases=["ub"])
@has_permission_or_fake("ban_members")
async def unban(ctx: commands.Context, user_id: int, *, reason: str = "No reason provided"):
    """Unbans a user by their ID."""
    try:
        user = await bot.fetch_user(user_id)
        await ctx.guild.unban(user, reason=reason)
        log_mod_action(ctx.guild.id, "UNBAN", user.id, ctx.author.id, reason)
        await ctx.send(f"{EMOJI_CHECKMARK} Successfully unbanned **{user}** | Reason: {reason}")
    except discord.NotFound:
        embed = discord.Embed(description=f"{EMOJI_CROSS} Ban not found or invalid User ID provided.", color=EMBED_COLOR)
        await ctx.send(embed=embed)

@bot.command(name="kick", aliases=["k"])
@has_permission_or_fake("kick_members")
async def kick(ctx: commands.Context, member: discord.Member, *, reason: str = "No reason provided"):
    """Kicks a member from the server."""
    if member.top_role >= ctx.author.top_role and ctx.author.id != ctx.guild.owner_id:
        embed = discord.Embed(description=f"{EMOJI_CROSS} You cannot kick someone with an equal or higher role than you.", color=EMBED_COLOR)
        return await ctx.send(embed=embed)

    await member.kick(reason=reason)
    log_mod_action(ctx.guild.id, "KICK", member.id, ctx.author.id, reason)
    await ctx.send(f"{EMOJI_HAMMER} Successfully kicked **{member}** | Reason: {reason}")

@bot.command(name="timeout", aliases=["mute", "to", "t"])
@has_permission_or_fake("moderate_members")
async def timeout(ctx: commands.Context, member: discord.Member, minutes: int, *, reason: str = "No reason provided"):
    """Times out a member for a given number of minutes."""
    if member.top_role >= ctx.author.top_role and ctx.author.id != ctx.guild.owner_id:
        embed = discord.Embed(description=f"{EMOJI_CROSS} You cannot timeout someone with an equal or higher role than you.", color=EMBED_COLOR)
        return await ctx.send(embed=embed)
    if minutes <= 0 or minutes > 40320:
        return await ctx.send(embed=get_syntax_embed("timeout"))

    duration = datetime.timedelta(minutes=minutes)
    await member.timeout(duration, reason=reason)
    log_mod_action(ctx.guild.id, "TIMEOUT", member.id, ctx.author.id, f"{minutes}m - {reason}")
    await ctx.send(f"{EMOJI_CLOCK} Timed out **{member}** for {minutes} minute(s) | Reason: {reason}")

@bot.command(name="untimeout", aliases=["unmute", "unto", "ut"])
@has_permission_or_fake("moderate_members")
async def untimeout(ctx: commands.Context, member: discord.Member, *, reason: str = "No reason provided"):
    """Removes a timeout from a member."""
    if not member.is_timed_out():
        embed = discord.Embed(description=f"{EMOJI_CROSS} **{member}** is not currently timed out.", color=EMBED_COLOR)
        return await ctx.send(embed=embed)

    await member.timeout(None, reason=reason)
    log_mod_action(ctx.guild.id, "UNTIMEOUT", member.id, ctx.author.id, reason)
    await ctx.send(f"{EMOJI_CHECKMARK} Removed timeout for **{member}** | Reason: {reason}")

@bot.command(name="warn", aliases=["w"])
@has_permission_or_fake("manage_messages")
async def warn(ctx: commands.Context, member: discord.Member, *, reason: str = "No reason provided"):
    """Logs a warning for a member."""
    add_warning(ctx.guild.id, member.id, ctx.author.id, reason)
    log_mod_action(ctx.guild.id, "WARN", member.id, ctx.author.id, reason)
    await ctx.send(f"{EMOJI_HAMMER} Warned **{member}** | Reason: {reason}")

@bot.command(name="warnings", aliases=["warns", "ws"])
@has_permission_or_fake("manage_messages")
async def warnings(ctx: commands.Context, member: discord.Member):
    """Displays warnings recorded for a member."""
    records = get_warnings(ctx.guild.id, member.id)
    if not records:
        embed = discord.Embed(description=f"ℹ️ **{member}** has no recorded warnings.", color=EMBED_COLOR)
        return await ctx.send(embed=embed)

    embed = discord.Embed(title=f"Warnings for {member.display_name}", color=EMBED_COLOR)
    for index, (warn_id, mod_id, reason, ts) in enumerate(records, start=1):
        mod = ctx.guild.get_member(mod_id)
        mod_name = str(mod) if mod else f"ID: {mod_id}"
        date_str = ts.split("T")[0]
        embed.add_field(
            name=f"#{index} (ID: {warn_id})",
            value=f"**Reason:** {reason}\n**Moderator:** {mod_name}\n**Date:** {date_str}",
            inline=False
        )
    await ctx.send(embed=embed)

@bot.command(name="clearwarnings", aliases=["clearwarns", "cw"])
@has_permission_or_fake("manage_messages")
async def clearwarnings(ctx: commands.Context, member: discord.Member):
    """Clears all warnings for a member."""
    count = clear_warnings(ctx.guild.id, member.id)
    await ctx.send(f"{EMOJI_CHECKMARK} Cleared {count} warning(s) for **{member}**.")

@bot.command(name="purge", aliases=["clear", "c"])
@has_permission_or_fake("manage_messages")
async def purge(ctx: commands.Context, amount: Optional[int] = None):
    """Purges messages from the current channel."""
    if amount is None or amount <= 0 or amount > 100:
        return await ctx.send(embed=get_syntax_embed("purge"))

    deleted = await ctx.channel.purge(limit=amount + 1)
    msg = await ctx.send(f"{EMOJI_TRASH} Purged {len(deleted) - 1} message(s).")
    await asyncio.sleep(3)
    try:
        await msg.delete()
    except discord.NotFound:
        pass

# ==========================================
# CONFIGURATION & FAKEPERMS COMMANDS
# ==========================================
@bot.group(name="fakeperms", aliases=["fp"], invoke_without_command=True)
@commands.has_permissions(administrator=True)
async def fakeperms(ctx: commands.Context):
    """Manage custom role permissions for bot commands."""
    await ctx.send(embed=get_syntax_embed("fakeperms"))

@fakeperms.command(name="add")
@commands.has_permissions(administrator=True)
async def fakeperms_add(ctx: commands.Context, role: discord.Role, command_name: str):
    """Grants a role access to run a specific command."""
    cmd = bot.get_command(command_name.lower())
    if not cmd:
        embed = discord.Embed(description=f"{EMOJI_CROSS} Command `{command_name}` does not exist.", color=EMBED_COLOR)
        return await ctx.send(embed=embed)

    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO fake_permissions (guild_id, role_id, command_name) VALUES (?, ?, ?)",
                       (ctx.guild.id, role.id, cmd.name.lower()))
        conn.commit()

    embed = discord.Embed(description=f"{EMOJI_CHECKMARK} Granted {role.mention} permission to use `!{cmd.name}`.", color=EMBED_COLOR)
    await ctx.send(embed=embed)

@fakeperms.command(name="remove", aliases=["rm"])
@commands.has_permissions(administrator=True)
async def fakeperms_remove(ctx: commands.Context, role: discord.Role, command_name: str):
    """Revokes access for a role to run a command."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM fake_permissions WHERE guild_id = ? AND role_id = ? AND command_name = ?",
                       (ctx.guild.id, role.id, command_name.lower()))
        deleted = cursor.rowcount
        conn.commit()

    if deleted > 0:
        embed = discord.Embed(description=f"{EMOJI_CHECKMARK} Removed permission for {role.mention} to use `!{command_name}`.", color=EMBED_COLOR)
    else:
        embed = discord.Embed(description=f"{EMOJI_CROSS} No fake permission rule existed for {role.mention} on `!{command_name}`.", color=EMBED_COLOR)
    await ctx.send(embed=embed)

@fakeperms.command(name="list")
@commands.has_permissions(administrator=True)
async def fakeperms_list(ctx: commands.Context):
    """Lists all active fake permission rules for this server."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT role_id, command_name FROM fake_permissions WHERE guild_id = ?", (ctx.guild.id,))
        rows = cursor.fetchall()

    if not rows:
        embed = discord.Embed(description=f"{EMOJI_INFO} No fake permissions configured for this server.", color=EMBED_COLOR)
        return await ctx.send(embed=embed)

    embed = discord.Embed(title=f"{EMOJI_GEARSET} Fake Permissions List", color=EMBED_COLOR)
    lines = []
    for rid, cname in rows:
        r = ctx.guild.get_role(rid)
        r_str = r.mention if r else f"Deleted Role ({rid})"
        lines.append(f"• {r_str} ➜ `!{cname}`")
    embed.description = "\n".join(lines)
    embed.set_footer(text="scyth • permissions")
    await ctx.send(embed=embed)

@bot.group(name="autoresponder", aliases=["ar"], invoke_without_command=True)
@has_permission_or_fake("manage_messages")
async def autoresponder(ctx: commands.Context):
    """Configure custom message triggers and responses."""
    await ctx.send(embed=get_syntax_embed("autoresponder"))

@autoresponder.command(name="add")
@has_permission_or_fake("manage_messages")
async def ar_add(ctx: commands.Context, *, content: str):
    """Adds a trigger and response. Format: !ar add trigger | response"""
    parts = [p.strip() for p in content.split("|")]
    if len(parts) < 2:
        return await ctx.send(embed=get_syntax_embed("autoresponder"))

    trigger, response = parts[0].lower(), parts[1]
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO autoresponders (guild_id, trigger, response) VALUES (?, ?, ?)",
                       (ctx.guild.id, trigger, response))
        conn.commit()

    embed = discord.Embed(description=f"{EMOJI_CHECKMARK} Added autoresponder for trigger: `{trigger}`", color=EMBED_COLOR)
    await ctx.send(embed=embed)

@autoresponder.command(name="remove", aliases=["rm", "del"])
@has_permission_or_fake("manage_messages")
async def ar_remove(ctx: commands.Context, *, trigger: str):
    """Deletes an autoresponder trigger."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM autoresponders WHERE guild_id = ? AND trigger = ?", (ctx.guild.id, trigger.lower().strip()))
        deleted = cursor.rowcount
        conn.commit()

    if deleted > 0:
        embed = discord.Embed(description=f"{EMOJI_CHECKMARK} Removed autoresponder for trigger: `{trigger}`", color=EMBED_COLOR)
    else:
        embed = discord.Embed(description=f"{EMOJI_CROSS} No trigger named `{trigger}` was found.", color=EMBED_COLOR)
    await ctx.send(embed=embed)

@autoresponder.command(name="list")
async def ar_list(ctx: commands.Context):
    """Lists all autoresponder triggers."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT trigger FROM autoresponders WHERE guild_id = ?", (ctx.guild.id,))
        rows = cursor.fetchall()

    if not rows:
        embed = discord.Embed(description=f"{EMOJI_INFO} No autoresponders configured.", color=EMBED_COLOR)
        return await ctx.send(embed=embed)

    triggers = [f"`{r[0]}`" for r in rows]
    embed = discord.Embed(title=f"{EMOJI_GEARSET} Autoresponder Triggers", description=", ".join(triggers), color=EMBED_COLOR)
    embed.set_footer(text=f"Total: {len(rows)} triggers • scyth")
    await ctx.send(embed=embed)

@bot.command(name="mediaonly")
@has_permission_or_fake("manage_channels")
async def mediaonly(ctx: commands.Context):
    """Toggles media-only enforcement on the current channel."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM media_only_channels WHERE guild_id = ? AND channel_id = ?",
                       (ctx.guild.id, ctx.channel.id))
        exists = cursor.fetchone()

        if exists:
            cursor.execute("DELETE FROM media_only_channels WHERE guild_id = ? AND channel_id = ?",
                           (ctx.guild.id, ctx.channel.id))
            conn.commit()
            embed = discord.Embed(description=f"{EMOJI_CHECKMARK} Disabled media-only mode for {ctx.channel.mention}.", color=EMBED_COLOR)
        else:
            cursor.execute("INSERT INTO media_only_channels (guild_id, channel_id) VALUES (?, ?)",
                           (ctx.guild.id, ctx.channel.id))
            conn.commit()
            embed = discord.Embed(description=f"{EMOJI_CHECKMARK} Enabled media-only mode for {ctx.channel.mention}. Non-media messages will be deleted.", color=EMBED_COLOR)
    await ctx.send(embed=embed)

# ==========================================
# UTILITY COMMANDS (SNIPE, CS, AVATAR, BANNER, ETC)
# ==========================================
@bot.command(name="snipe", aliases=["s"])
@commands.has_permissions(manage_messages=True)
async def snipe(ctx: commands.Context):
    """Snipes the most recently deleted message in this channel."""
    data = sniped_messages.get(ctx.channel.id)
    if not data:
        embed = discord.Embed(description=f"{EMOJI_CROSS} There are no recently deleted messages to snipe in this channel.", color=EMBED_COLOR)
        return await ctx.send(embed=embed)

    embed = discord.Embed(
        description=data["content"] or "*Message had no text content*",
        color=EMBED_COLOR,
        timestamp=data["timestamp"]
    )
    embed.set_author(name=str(data["author"]), icon_url=data["author"].display_avatar.url)
    if data["attachment"]:
        embed.set_image(url=data["attachment"])
    embed.set_footer(text="scyth • snipe")
    await ctx.send(embed=embed)

@bot.command(name="editsnipe", aliases=["es"])
@commands.has_permissions(manage_messages=True)
async def editsnipe(ctx: commands.Context):
    """Snipes the original pre-edited content of the last modified message."""
    data = edited_messages.get(ctx.channel.id)
    if not data:
        embed = discord.Embed(description=f"{EMOJI_CROSS} There are no recently edited messages to snipe in this channel.", color=EMBED_COLOR)
        return await ctx.send(embed=embed)

    embed = discord.Embed(
        title="Edited Message Snipe",
        description=f"**Before:**\n> {data['before']}\n\n**After:**\n> {data['after']}",
        color=EMBED_COLOR,
        timestamp=data["timestamp"]
    )
    embed.set_author(name=str(data["author"]), icon_url=data["author"].display_avatar.url)
    embed.set_footer(text="scyth • editsnipe")
    await ctx.send(embed=embed)

@bot.command(name="clearsnipe", aliases=["cs"])
@has_permission_or_fake("manage_messages")
async def clearsnipe(ctx: commands.Context):
    """Clears both deleted and edited message history for this channel."""
    sniped_messages.pop(ctx.channel.id, None)
    edited_messages.pop(ctx.channel.id, None)
    embed = discord.Embed(description=f"{EMOJI_TRASH} Cleared all cached deleted and edited messages for this channel.", color=EMBED_COLOR)
    await ctx.send(embed=embed)

@bot.command(name="avatar", aliases=["av"])
async def avatar(ctx: commands.Context, member: Optional[discord.Member] = None):
    """Displays a member's global profile avatar."""
    target = member or ctx.author
    embed = discord.Embed(title=f"{target.display_name}'s Avatar", color=EMBED_COLOR)
    embed.set_image(url=target.display_avatar.url)
    embed.set_footer(text=f"Requested by {ctx.author.name} • scyth")
    await ctx.send(embed=embed)

@bot.command(name="sav", aliases=["serveravatar"])
async def sav(ctx: commands.Context, member: Optional[discord.Member] = None):
    """Displays a member's server-specific avatar."""
    target = member or ctx.author
    if not target.guild_avatar:
        embed = discord.Embed(description=f"{EMOJI_CROSS} **{target.display_name}** does not have a server-specific avatar.", color=EMBED_COLOR)
        return await ctx.send(embed=embed)

    embed = discord.Embed(title=f"{target.display_name}'s Server Avatar", color=EMBED_COLOR)
    embed.set_image(url=target.guild_avatar.url)
    embed.set_footer(text=f"Requested by {ctx.author.name} • scyth")
    await ctx.send(embed=embed)

@bot.command(name="banner")
async def banner(ctx: commands.Context, user: Optional[discord.User] = None):
    """Displays a user's Discord profile banner."""
    target = await bot.fetch_user(user.id if user else ctx.author.id)
    if not target.banner:
        embed = discord.Embed(description=f"{EMOJI_CROSS} **{target.name}** does not have a custom profile banner.", color=EMBED_COLOR)
        return await ctx.send(embed=embed)

    embed = discord.Embed(title=f"{target.name}'s Banner", color=EMBED_COLOR)
    embed.set_image(url=target.banner.url)
    embed.set_footer(text=f"Requested by {ctx.author.name} • scyth")
    await ctx.send(embed=embed)

@bot.command(name="sbanner", aliases=["serverbanner"])
async def sbanner(ctx: commands.Context):
    """Displays the server banner."""
    if not ctx.guild.banner:
        embed = discord.Embed(description=f"{EMOJI_CROSS} This server does not have a banner set.", color=EMBED_COLOR)
        return await ctx.send(embed=embed)

    embed = discord.Embed(title=f"{ctx.guild.name}'s Banner", color=EMBED_COLOR)
    embed.set_image(url=ctx.guild.banner.url)
    embed.set_footer(text=f"Requested by {ctx.author.name} • scyth")
    await ctx.send(embed=embed)

@bot.command(name="firstmessage", aliases=["firstmsg", "fm", "jump"])
async def firstmessage(ctx: commands.Context):
    """Finds and links to the very first message sent in this channel."""
    first = None
    async for msg in ctx.channel.history(limit=1, oldest_first=True):
        first = msg
        break

    if not first:
        embed = discord.Embed(description=f"{EMOJI_CROSS} No messages found in this channel.", color=EMBED_COLOR)
        return await ctx.send(embed=embed)

    embed = discord.Embed(
        title="First Message",
        description=f"**Author:** {first.author.mention}\n**Sent:** <t:{int(first.created_at.timestamp())}:R>\n\n> {first.content[:200] if first.content else '*No text content*'}",
        color=EMBED_COLOR
    )
    embed.set_footer(text="scyth • utility")

    view = View()
    view.add_item(Button(label="Jump to Message", url=first.jump_url, style=discord.ButtonStyle.link))
    await ctx.send(embed=embed, view=view)

@bot.command(name="membercount", aliases=["mc"])
async def membercount(ctx: commands.Context):
    """Displays clean server member count statistics."""
    guild = ctx.guild
    humans = len([m for m in guild.members if not m.bot])
    bots = len([m for m in guild.members if m.bot])
    total = guild.member_count

    embed = discord.Embed(title=f"{guild.name} Member Count", color=EMBED_COLOR)
    embed.add_field(name="Total Members", value=f"**{total:,}**", inline=True)
    embed.add_field(name="Humans", value=f"**{humans:,}**", inline=True)
    embed.add_field(name="Bots", value=f"**{bots:,}**", inline=True)
    embed.set_footer(text="scyth • statistics")
    await ctx.send(embed=embed)

@bot.command(name="nuke", aliases=["wipe", "n"])
@commands.has_permissions(manage_channels=True)
async def nuke(ctx: commands.Context):
    """Clones and deletes the current channel to wipe all chat history."""
    channel = ctx.channel
    pos = channel.position
    new_channel = await channel.clone(reason=f"Nuked by {ctx.author}")
    await channel.delete(reason=f"Nuked by {ctx.author}")
    await new_channel.edit(position=pos)

    embed = discord.Embed(
        title="Channel Nuked",
        description="This channel has been wiped and reset.",
        color=EMBED_COLOR
    )
    embed.set_image(url="https://media.giphy.com/media/oe33xf3B50fsc/giphy.gif")
    embed.set_footer(text=f"Triggered by {ctx.author.name} • scyth")
    await new_channel.send(embed=embed)

@bot.command(name="embed", aliases=["say", "em"])
@commands.has_permissions(manage_messages=True)
async def embed_command(ctx: commands.Context, *, content: Optional[str] = None):
    """Creates a custom embed. Format: !embed Title | Description | HexColor(Optional)"""
    if not content:
        return await ctx.send(embed=get_syntax_embed("embed"))

    parts = [p.strip() for p in content.split("|")]
    if len(parts) < 2:
        return await ctx.send(embed=get_syntax_embed("embed"))

    title, description = parts[0], parts[1]
    color = EMBED_COLOR

    if len(parts) >= 3:
        raw_color = parts[2].replace("#", "")
        try:
            color = int(raw_color, 16)
        except ValueError:
            pass

    embed_obj = discord.Embed(title=title, description=description, color=color)
    embed_obj.set_footer(text=f"{EMOJI_PENCIL} Requested by {ctx.author.display_name} • scyth", icon_url=ctx.author.display_avatar.url)
    await ctx.send(embed=embed_obj)

@bot.command(name="serverinfo", aliases=["sinfo", "si", "guildinfo"])
async def serverinfo(ctx: commands.Context):
    """Displays information about the server."""
    guild = ctx.guild
    embed = discord.Embed(title=guild.name, color=EMBED_COLOR)
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)

    embed.add_field(name="Server ID", value=guild.id, inline=True)
    embed.add_field(name="Owner", value=str(guild.owner), inline=True)
    embed.add_field(name="Created On", value=guild.created_at.strftime("%b %d, %Y"), inline=True)
    embed.add_field(name="Members", value=guild.member_count, inline=True)
    embed.add_field(name="Channels", value=f"{len(guild.text_channels)} Text | {len(guild.voice_channels)} Voice", inline=True)
    embed.add_field(name="Roles", value=len(guild.roles), inline=True)
    embed.set_footer(text=f"Requested by {ctx.author.name} • scyth")
    await ctx.send(embed=embed)

@bot.command(name="channelinfo", aliases=["cinfo", "ci"])
async def channelinfo(ctx: commands.Context, channel: Optional[discord.TextChannel] = None):
    """Displays information about a text channel."""
    ch = channel or ctx.channel
    embed = discord.Embed(title=f"#{ch.name}", color=EMBED_COLOR)
    embed.add_field(name="Channel ID", value=ch.id, inline=True)
    embed.add_field(name="Category", value=ch.category.name if ch.category else "None", inline=True)
    embed.add_field(name="Position", value=ch.position, inline=True)
    embed.add_field(name="Created On", value=ch.created_at.strftime("%b %d, %Y"), inline=True)
    embed.add_field(name="NSFW", value="Yes" if ch.is_nsfw() else "No", inline=True)
    embed.add_field(name="Topic", value=ch.topic or "None set", inline=False)
    embed.set_footer(text="scyth utility")
    await ctx.send(embed=embed)

@bot.command(name="userinfo", aliases=["uinfo", "ui", "whois"])
async def userinfo(ctx: commands.Context, member: Optional[discord.Member] = None):
    """Displays information about a server member."""
    target = member or ctx.author
    embed = discord.Embed(title=f"User Info — {target}", color=EMBED_COLOR)
    embed.set_thumbnail(url=target.display_avatar.url)
    embed.add_field(name="User ID", value=target.id, inline=True)
    embed.add_field(name="Bot Account?", value="Yes" if target.bot else "No", inline=True)
    embed.add_field(name="Created On", value=target.created_at.strftime("%b %d, %Y"), inline=True)
    embed.add_field(name="Joined Server", value=target.joined_at.strftime("%b %d, %Y") if target.joined_at else "Unknown", inline=True)

    roles = [r.mention for r in reversed(target.roles) if not r.is_default()]
    roles_str = " ".join(roles) if roles else "No custom roles"
    embed.add_field(name=f"Roles ({len(roles)})", value=roles_str[:1024], inline=False)
    embed.set_footer(text="scyth utility")
    await ctx.send(embed=embed)

@bot.command(name="lock")
@commands.has_permissions(manage_channels=True)
async def lock(ctx: commands.Context):
    """Locks the current channel so regular members cannot send messages."""
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False)
    embed = discord.Embed(
        title="Channel Locked",
        description=f"{EMOJI_LOCK} This channel has been locked by {ctx.author.mention}.",
        color=EMBED_COLOR
    )
    embed.set_footer(text="scyth • moderation")
    await ctx.send(embed=embed)

@bot.command(name="unlock")
@commands.has_permissions(manage_channels=True)
async def unlock(ctx: commands.Context):
    """Unlocks the current channel so regular members can send messages again."""
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=True)
    embed = discord.Embed(
        title="Channel Unlocked",
        description=f"{EMOJI_UNLOCK} This channel has been unlocked by {ctx.author.mention}.",
        color=EMBED_COLOR
    )
    embed.set_footer(text="scyth • moderation")
    await ctx.send(embed=embed)

# ==========================================
# INTERACTIVE DROPDOWN HELP COMMAND (FIXED EMOJIS & SERVER NAME)
# ==========================================
HELP_CATEGORIES = {
    "moderation": {
        "title": f"{EMOJI_HAMMER} Moderation Commands",
        "desc": "Full moderation suite with role protection and SQLite logging.",
        "commands": [
            "`!ban <member> [reason]` — Ban user",
            "`!unban <id> [reason]` — Unban by ID",
            "`!kick <member> [reason]` — Kick member",
            "`!jail <member> [reason]` — Isolate member and store roles",
            "`!unjail <member>` — Restore roles and unjail",
            "`!strip <member>` — Strip all roles and save them",
            "`!restore <member>` — Restore stripped roles",
            "`!hardban <id> [reason]` — Permanent auto-reban blacklist",
            "`!role <member> <role>` — Fast role toggle",
            "`!timeout <member> <min>` — Mute member",
            "`!untimeout <member>` — Remove timeout",
            "`!warn <member> [reason]` — Issue formal warning",
            "`!warnings <member>` — View warning history",
            "`!clearwarnings <member>` — Clear all warnings",
            "`!purge <1-100>` — Delete recent messages"
        ]
    },
    "music": {
        "title": f"{EMOJI_DISC} Music Commands",
        "desc": "High-fidelity Lavalink streaming with auto-failover and playlists.",
        "commands": [
            "`!play <query/url>` — Stream track or Spotify playlist",
            "`!playnext <query>` — Insert track to the front of queue",
            "`!pause` / `!resume` — Pause or continue audio",
            "`!skip` — Skip currently playing track",
            "`!queue` — View server playback queue",
            "`!clearqueue` — Wipe queue and cancel loaders",
            "`!shuffle` — Randomize queue order",
            "`!volume <1-100>` — Adjust loudness",
            "`!autoplay` — Toggle recommendation engine",
            "`!stop` — Disconnect bot and clear queue"
        ]
    },
    "security": {
        "title": f"{EMOJI_SHIELD} Security & Anti-Nuke",
        "desc": "Automated server protection, rate limits, and wipers.",
        "commands": [
            "`!lock` / `!unlock` — Freeze or open text channel",
            "`!mediaonly` — Toggle media-only channel enforcement",
            "`!nuke` — Clone and wipe current channel",
            "`!autonuke set <min>` — Setup automatic channel wiper",
            "`!autonuke remove` — Disable scheduled auto-nuke",
            "`Anti-Nuke Engine` — Instant ban on mass channel/role deletes",
            "`Anti-Raid Engine` — Kicks mass joins (>5 in 10s)",
            "`Anti-Spam Engine` — 5-minute timeout for message flooding",
            "`Anti-Invite Engine` — Auto-deletes discord.gg invite links"
        ]
    },
    "voicemaster": {
        "title": f"{EMOJI_SPEAKER} VoiceMaster Controls",
        "desc": "Dynamic Join-to-Create voice channels with persistent buttons.",
        "commands": [
            "`!voicemaster setup` — Configure category & interface",
            f"{EMOJI_LOCK} `Lock` / {EMOJI_UNLOCK} `Unlock` — Control entry permissions",
            f"{EMOJI_GHOST} `Hide` / {EMOJI_UNGHOST} `Unhide` — Toggle channel visibility",
            f"{EMOJI_PENCIL} `Rename` — Customize room name via modal dialog",
            f"{EMOJI_INCREASE} `Capacity` — Set user limits (0-99)",
            f"{EMOJI_CLAIM} `Claim` — Take ownership if original host leaves",
            f"{EMOJI_ACTIVITY} `Activity` — Launch YouTube Watch Together"
        ]
    },
    "utility": {
        "title": f"{EMOJI_PENCIL} Utility & Social",
        "desc": "Profiles, banners, custom embeds, and tools.",
        "commands": [
            "`!avatar [member]` — View user avatar",
            "`!sav [member]` — View server-specific avatar",
            "`!banner [user]` — View user profile banner",
            "`!sbanner` — View guild server banner",
            "`!snipe` — Retrieve last deleted message",
            "`!editsnipe` — Retrieve last edited message",
            "`!clearsnipe` — Wipe channel snipe cache",
            "`!firstmessage` — Jump to channel's first message",
            "`!membercount` — View server member counts",
            "`!afk [reason]` — Set away status with auto-notify",
            "`!embed <title> | <desc>` — Create dark custom embeds",
            "`!serverinfo` — Server statistics overview",
            "`!channelinfo` — Current channel details",
            "`!userinfo [member]` — Detailed account info"
        ]
    },
    "config": {
        "title": f"{EMOJI_GEARSET} Configuration",
        "desc": "Custom server permissions and auto-responder rules.",
        "commands": [
            "`!fakeperms add <@role> <cmd>` — Grant role command access",
            "`!fakeperms remove <@role> <cmd>` — Revoke role command access",
            "`!fakeperms list` — View all fake permission mappings",
            "`!ar add <trigger> | <response>` — Add auto-responder",
            "`!ar remove <trigger>` — Delete auto-responder",
            "`!ar list` — View active triggers"
        ]
    }
}

class HelpSelect(Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label="Moderation", 
                emoji=discord.PartialEmoji.from_str(EMOJI_HAMMER), 
                value="moderation", 
                description="Bans, jails, strips, and timeouts"
            ),
            discord.SelectOption(
                label="Music", 
                emoji=discord.PartialEmoji.from_str(EMOJI_DISC), 
                value="music", 
                description="Lavalink playback, queues, and playlists"
            ),
            discord.SelectOption(
                label="Security", 
                emoji=discord.PartialEmoji.from_str(EMOJI_SHIELD), 
                value="security", 
                description="Anti-nuke, anti-raid, and auto-nuke wipers"
            ),
            discord.SelectOption(
                label="VoiceMaster", 
                emoji=discord.PartialEmoji.from_str(EMOJI_SPEAKER), 
                value="voicemaster", 
                description="Join-to-Create voice interface controls"
            ),
            discord.SelectOption(
                label="Utility", 
                emoji=discord.PartialEmoji.from_str(EMOJI_PENCIL), 
                value="utility", 
                description="Avatars, banners, snipes, and stats"
            ),
            discord.SelectOption(
                label="Configuration", 
                emoji=discord.PartialEmoji.from_str(EMOJI_GEARSET), 
                value="config", 
                description="Fake permissions and auto-responders"
            ),
        ]
        super().__init__(placeholder="Select a command category...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        cat_key = self.values[0]
        cat = HELP_CATEGORIES[cat_key]

        embed = discord.Embed(
            title=cat["title"],
            description=f"{cat['desc']}\n\n" + "\n".join(cat["commands"]),
            color=EMBED_COLOR
        )
        embed.set_footer(text=f"Category: {self.values[0].capitalize()} • scyth", icon_url=interaction.client.user.display_avatar.url)
        await interaction.response.edit_message(embed=embed, view=self.view)

class HelpView(View):
    def __init__(self, author_id: int):
        super().__init__(timeout=180)
        self.author_id = author_id
        self.add_item(HelpSelect())

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("Only the person who requested this menu can interact with it.", ephemeral=True)
            return False
        return True

@bot.command(name="help", aliases=["h"])
async def help_command(ctx: commands.Context):
    """Displays the interactive categorized help menu."""
    server_name = ctx.guild.name if ctx.guild else "Scyth"
    embed = discord.Embed(
        title=f"Scyth • Command Center",
        description=(
            f"Welcome to **{server_name}**. Use the dropdown menu below to explore commands across all categories.\n\n"
            f"> {EMOJI_HAMMER} **Moderation** — Staff actions, jail, role strip, hardban\n"
            f"> {EMOJI_DISC} **Music** — Lavalink streaming, autoplay, playlists\n"
            f"> {EMOJI_SHIELD} **Security** — Anti-nuke, anti-raid, channel locks\n"
            f"> {EMOJI_SPEAKER} **VoiceMaster** — Dynamic temporary voice channels\n"
            f"> {EMOJI_PENCIL} **Utility** — Avatars, banners, snipes, stats\n"
            f"> {EMOJI_GEARSET} **Config** — Fake permissions, auto-responders\n\n"
            f"*Prefix:* `{ctx.prefix}` • Select a category below to view commands."
        ),
        color=EMBED_COLOR
    )
    if ctx.guild and ctx.guild.icon:
        embed.set_thumbnail(url=ctx.guild.icon.url)
    embed.set_footer(text="scyth • help menu", icon_url=bot.user.display_avatar.url)

    view = HelpView(ctx.author.id)
    await ctx.send(embed=embed, view=view)

# ==========================================
# GLOBAL ERROR HANDLER
# ==========================================
@bot.event
async def on_command_error(ctx: commands.Context, error: Exception):
    if isinstance(error, commands.CommandNotFound):
        return

    if isinstance(error, (commands.MissingRequiredArgument, commands.BadArgument)):
        cmd_key = ctx.command.root_parent.name if ctx.command.root_parent else ctx.command.name
        syntax_embed = get_syntax_embed(cmd_key)
        if syntax_embed:
            return await ctx.send(embed=syntax_embed)

    if isinstance(error, commands.MissingPermissions):
        perms = ", ".join(error.missing_permissions)
        embed = discord.Embed(
            title="Missing Permissions",
            description=f"{EMOJI_CROSS} You lack the required permission(s): `{perms}`",
            color=EMBED_COLOR
        )
        return await ctx.send(embed=embed)

    if isinstance(error, commands.BotMissingPermissions):
        perms = ", ".join(error.missing_permissions)
        embed = discord.Embed(
            title="Bot Missing Permissions",
            description=f"{EMOJI_CROSS} I lack the required permission(s) to execute this: `{perms}`",
            color=EMBED_COLOR
        )
        return await ctx.send(embed=embed)

    if isinstance(error, commands.CommandOnCooldown):
        embed = discord.Embed(
            title="Cooldown Active",
            description=f"{EMOJI_CLOCK} Please wait `{error.retry_after:.1f}s` before using this command again.",
            color=EMBED_COLOR
        )
        return await ctx.send(embed=embed)

    print(f"Unhandled Exception in command {ctx.command}: {error}")

# ==========================================
# SCRIPT EXECUTION
# ==========================================
if __name__ == "__main__":
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE" or not BOT_TOKEN:
        print("Please set the DISCORD_TOKEN environment variable or replace YOUR_BOT_TOKEN_HERE.")
    else:
        bot.run(BOT_TOKEN)