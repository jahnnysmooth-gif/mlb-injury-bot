import os
import asyncio
import re
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import discord
import requests
from bs4 import BeautifulSoup

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID", "0"))
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "900"))

ESPN_URL = "https://www.espn.com/mlb/injuries"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/145.0.0.0 Safari/537.36"
    )
}

TEAM_NAME_TO_ABBR = {
    "Arizona Diamondbacks": "ARI",
    "Athletics": "ATH",
    "Atlanta Braves": "ATL",
    "Baltimore Orioles": "BAL",
    "Boston Red Sox": "BOS",
    "Chicago Cubs": "CHC",
    "Chicago White Sox": "CWS",
    "Cincinnati Reds": "CIN",
    "Cleveland Guardians": "CLE",
    "Colorado Rockies": "COL",
    "Detroit Tigers": "DET",
    "Houston Astros": "HOU",
    "Kansas City Royals": "KC",
    "Los Angeles Angels": "LAA",
    "Los Angeles Dodgers": "LAD",
    "Miami Marlins": "MIA",
    "Milwaukee Brewers": "MIL",
    "Minnesota Twins": "MIN",
    "New York Mets": "NYM",
    "New York Yankees": "NYY",
    "Philadelphia Phillies": "PHI",
    "Pittsburgh Pirates": "PIT",
    "San Diego Padres": "SD",
    "San Francisco Giants": "SF",
    "Seattle Mariners": "SEA",
    "St. Louis Cardinals": "STL",
    "Tampa Bay Rays": "TB",
    "Texas Rangers": "TEX",
    "Toronto Blue Jays": "TOR",
    "Washington Nationals": "WSH",
}

TEAM_COLORS = {
    "ARI": 0xA71930,
    "ATH": 0x003831,
    "ATL": 0xCE1141,
    "BAL": 0xDF4601,
    "BOS": 0xBD3039,
    "CHC": 0x0E3386,
    "CWS": 0x27251F,
    "CIN": 0xC6011F,
    "CLE": 0xE31937,
    "COL": 0x33006F,
    "DET": 0x0C2340,
    "HOU": 0xEB6E1F,
    "KC": 0x004687,
    "LAA": 0xBA0021,
    "LAD": 0x005A9C,
    "MIA": 0x00A3E0,
    "MIL": 0x12284B,
    "MIN": 0x002B5C,
    "NYM": 0x002D72,
    "NYY": 0x132448,
    "PHI": 0xE81828,
    "PIT": 0xFDB827,
    "SD": 0x2F241D,
    "SF": 0xFD5A1E,
    "SEA": 0x0C2C56,
    "STL": 0xC41E3A,
    "TB": 0x092C5C,
    "TEX": 0x003278,
    "TOR": 0x134A8E,
    "WSH": 0xAB0003,
}

TEAM_LOGOS = {
    "ARI": "https://a.espncdn.com/i/teamlogos/mlb/500/ari.png",
    "ATH": "https://a.espncdn.com/i/teamlogos/mlb/500/oak.png",
    "ATL": "https://a.espncdn.com/i/teamlogos/mlb/500/atl.png",
    "BAL": "https://a.espncdn.com/i/teamlogos/mlb/500/bal.png",
    "BOS": "https://a.espncdn.com/i/teamlogos/mlb/500/bos.png",
    "CHC": "https://a.espncdn.com/i/teamlogos/mlb/500/chc.png",
    "CWS": "https://a.espncdn.com/i/teamlogos/mlb/500/chw.png",
    "CIN": "https://a.espncdn.com/i/teamlogos/mlb/500/cin.png",
    "CLE": "https://a.espncdn.com/i/teamlogos/mlb/500/cle.png",
    "COL": "https://a.espncdn.com/i/teamlogos/mlb/500/col.png",
    "DET": "https://a.espncdn.com/i/teamlogos/mlb/500/det.png",
    "HOU": "https://a.espncdn.com/i/teamlogos/mlb/500/hou.png",
    "KC": "https://a.espncdn.com/i/teamlogos/mlb/500/kc.png",
    "LAA": "https://a.espncdn.com/i/teamlogos/mlb/500/laa.png",
    "LAD": "https://a.espncdn.com/i/teamlogos/mlb/500/lad.png",
    "MIA": "https://a.espncdn.com/i/teamlogos/mlb/500/mia.png",
    "MIL": "https://a.espncdn.com/i/teamlogos/mlb/500/mil.png",
    "MIN": "https://a.espncdn.com/i/teamlogos/mlb/500/min.png",
    "NYM": "https://a.espncdn.com/i/teamlogos/mlb/500/nym.png",
    "NYY": "https://a.espncdn.com/i/teamlogos/mlb/500/nyy.png",
    "PHI": "https://a.espncdn.com/i/teamlogos/mlb/500/phi.png",
    "PIT": "https://a.espncdn.com/i/teamlogos/mlb/500/pit.png",
    "SD": "https://a.espncdn.com/i/teamlogos/mlb/500/sd.png",
    "SF": "https://a.espncdn.com/i/teamlogos/mlb/500/sf.png",
    "SEA": "https://a.espncdn.com/i/teamlogos/mlb/500/sea.png",
    "STL": "https://a.espncdn.com/i/teamlogos/mlb/500/stl.png",
    "TB": "https://a.espncdn.com/i/teamlogos/mlb/500/tb.png",
    "TEX": "https://a.espncdn.com/i/teamlogos/mlb/500/tex.png",
    "TOR": "https://a.espncdn.com/i/teamlogos/mlb/500/tor.png",
    "WSH": "https://a.espncdn.com/i/teamlogos/mlb/500/wsh.png",
}

VALID_POSITIONS = {
    "SP", "RP", "P", "C", "1B", "2B", "3B", "SS",
    "LF", "CF", "RF", "OF", "DH", "INF", "UTIL"
}

VALID_STATUSES = {
    "60-Day-IL",
    "15-Day-IL",
    "10-Day-IL",
    "7-Day-IL",
    "Day-To-Day",
    "Out",
    "Suspension",
    "Bereavement",
    "Paternity",
}

DEFAULT_COLOR = 0x5865F2
MAX_UPDATE_LEN = 220
RECENT_DAYS = 1


def clean_text(text: str) -> str:
    return " ".join(text.split()).strip()


def clamp_update(text: str, max_len: int = MAX_UPDATE_LEN) -> str:
    text = clean_text(text)
    if len(text) <= max_len:
        return text
    return text[: max_len - 1].rstrip() + "…"


def short_date(date_str: str) -> str:
    for fmt in ("%b %d", "%b %d, %Y", "%B %d", "%B %d, %Y"):
        try:
            dt = datetime.strptime(date_str, fmt)
            if "%Y" not in fmt:
                dt = dt.replace(year=datetime.now().year)
            return dt.strftime("%b %d")
        except ValueError:
            continue
    return date_str


def should_run_now() -> bool:
    now_et = datetime.now(ZoneInfo("America/New_York"))
    return 7 <= now_et.hour < 24


def fetch_html() -> str:
    response = requests.get(ESPN_URL, headers=HEADERS, timeout=30)
    response.raise_for_status()
    return response.text


def parse_comment_date(comment: str) -> datetime | None:
    match = re.match(r"^([A-Z][a-z]{2}\s+\d{1,2}):", comment)
    if not match:
        return None

    month_day = match.group(1)
    now_et = datetime.now(ZoneInfo("America/New_York"))

    for year in (now_et.year, now_et.year - 1):
        try:
            dt = datetime.strptime(f"{month_day} {year}", "%b %d %Y")
            return dt.replace(tzinfo=ZoneInfo("America/New_York"))
        except ValueError:
            continue

    return None


def is_recent_update(comment: str, days: int = RECENT_DAYS) -> bool:
    comment_dt = parse_comment_date(comment)
    if comment_dt is None:
        return False

    now_et = datetime.now(ZoneInfo("America/New_York"))
    cutoff = now_et - timedelta(days=days)
    return comment_dt >= cutoff


def parse_espn_injuries(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    lines = [clean_text(x) for x in soup.get_text("\n").splitlines()]
    lines = [x for x in lines if x]

    items = []
    team_names = set(TEAM_NAME_TO_ABBR.keys())

    try:
        start_index = lines.index("hidden") + 1
    except ValueError:
        start_index = 0

    i = start_index
    current_team = None

    while i < len(lines):
        line = lines[i]

        if line in team_names:
            current_team = line
            i += 1

            while i < len(lines) and lines[i] in {
                "NAME",
                "POS",
                "EST. RETURN DATE",
                "STATUS",
                "COMMENT",
            }:
                i += 1
            continue

        if not current_team:
            i += 1
            continue

        if i + 4 >= len(lines):
            break

        player = lines[i]
        position = lines[i + 1]
        est_return = lines[i + 2]
        status = lines[i + 3]
        comment = lines[i + 4]

        if player in team_names:
            current_team = player
            i += 1
            continue

        if (
            position in VALID_POSITIONS
            and status in VALID_STATUSES
            and ":" in comment
            and is_recent_update(comment)
        ):
            items.append({
                "team_name": current_team,
                "team": TEAM_NAME_TO_ABBR[current_team],
                "player": player,
                "position": position,
                "est_return": est_return,
                "status": status,
                "comment": comment,
            })
            i += 5
        else:
            i += 1

    return items


def build_embed(item: dict) -> discord.Embed:
    team = item["team"]
    color = TEAM_COLORS.get(team, DEFAULT_COLOR)
    logo_url = TEAM_LOGOS.get(team)

    title = "🚑 MLB INJURY UPDATE"
    if item["status"] == "60-Day-IL":
        title = "🧊 60-DAY IL"
    elif item["status"] == "Day-To-Day":
        title = "⚠️ DAY-TO-DAY"
    elif "IL" in item["status"]:
        title = "🚨 IL PLACEMENT"

    embed = discord.Embed(title=title, color=color)
    embed.description = f"**{item['player']}**\n`{team} • {item['position']}`"
    embed.add_field(name="Status", value=f"`{item['status']}`", inline=True)
    embed.add_field(name="Est. Return", value=f"`{short_date(item['est_return'])}`", inline=True)
    embed.add_field(name="Source", value="`ESPN`", inline=True)
    embed.add_field(name="Update", value=clamp_update(item["comment"]), inline=False)

    if logo_url:
        embed.set_thumbnail(url=logo_url)

    embed.set_footer(text="ESPN MLB Injuries")
    return embed


intents = discord.Intents.default()
client = discord.Client(intents=intents)


async def post_recent_updates() -> None:
    channel = client.get_channel(CHANNEL_ID)
    if channel is None:
        print("[BOT] Channel not found.")
        return

    try:
        html = fetch_html()
        items = parse_espn_injuries(html)
        print(f"[BOT] Parsed {len(items)} recent injury items")
    except Exception as e:
        print(f"[BOT] Failed to fetch/parse ESPN page: {e}")
        return

    if not items:
        print("[BOT] No recent items found.")
        return

    # oldest to newest by comment date
    items.sort(key=lambda x: parse_comment_date(x["comment"]) or datetime.min.replace(tzinfo=ZoneInfo("America/New_York")))

    for item in items:
        try:
            embed = build_embed(item)
            await channel.send(embed=embed)
            print(f"[BOT] Posted: {item['player']} | {item['team']} | {item['status']}")
            await asyncio.sleep(1.0)
        except Exception as e:
            print(f"[BOT] Failed to post {item['player']}: {e}")


async def background_loop() -> None:
    await client.wait_until_ready()
    print("[BOT] ESPN injury bot started")

    while not client.is_closed():
        if should_run_now():
            print("[BOT] Running injury check")
            await post_recent_updates()
        else:
            print("[BOT] Outside allowed hours. Skipping check.")

        await asyncio.sleep(POLL_INTERVAL)


@client.event
async def on_ready():
    print(f"[BOT] Logged in as {client.user}")
    asyncio.create_task(background_loop())


async def main():
    if not DISCORD_TOKEN:
        raise RuntimeError("DISCORD_TOKEN is not set")
    if not CHANNEL_ID:
        raise RuntimeError("CHANNEL_ID is not set")
    await client.start(DISCORD_TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
