import requests
from datetime import datetime
import json
from bs4 import BeautifulSoup
import discord
from discord import app_commands
from discord.ext import tasks
import os

URL = "https://menu.matildaplatform.com/sv/meals/67e546daea58e3e60cfcc680"
URLWEEK = "https://menu.matildaplatform.com/embed?displayMode=Week&distributorId=67e546daea58e3e60cfcc680"
role_id = 1360735590190022665

allowed_mentions = discord.AllowedMentions(everyone=True, roles=True)


def get_current_date():
    """Return today's date as a string (called fresh each time so it's always accurate)."""
    return datetime.now().strftime('%Y-%m-%d')


def get_foodWeekly():
    page = requests.get(URLWEEK)
    soup = BeautifulSoup(page.text, 'html.parser')
    script_tag = soup.find('script', {'id': '__NEXT_DATA__'})
    data = json.loads(script_tag.string)
    meals = data['props']['pageProps']['meals']
    return meals


def get_foodToday():
    headers = {'Content-Type': 'application/json'}
    data = {'date': get_current_date()}
    response = requests.post(URL, headers=headers, json=data)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        script_tag = soup.find("script", id="__NEXT_DATA__")
        if script_tag:
            try:
                return json.loads(script_tag.string)
            except json.JSONDecodeError as e:
                return {"error": "Failed to decode JSON", "details": str(e)}
        else:
            return {"error": "No '__NEXT_DATA__' script tag found."}
    else:
        return {"error": f"Failed to fetch data, status code: {response.status_code}"}


def build_today_embed():
    """Build the embed for today's food menu, grouping both options under one heading."""
    food_data = get_foodToday()
    food_description = ""

    if "props" in food_data:
        try:
            meals = food_data["props"]["pageProps"]["meals"]

            # Group courses by date (same logic as weekly)
            grouped = {}
            for meal in meals:
                try:
                    date_str = meal.get("date", "unknown")
                    date_obj = datetime.fromisoformat(date_str)
                    weekday = date_obj.strftime('%A')
                    date_display = date_obj.strftime('%Y-%m-%d')
                    week_num = date_obj.isocalendar().week
                    if date_str not in grouped:
                        grouped[date_str] = {"name": weekday, "week": week_num, "courses": []}
                    for course in meal.get("courses", []):
                        grouped[date_str]["courses"].append(course["name"])
                except Exception:
                    pass

            for date_str, info in grouped.items():
                food_description += f"**{info['name']}** - Week {info['week']}:\n"
                if info["courses"]:
                    for course in info["courses"]:
                        food_description += f"• {course}\n"
                else:
                    food_description += "• No lunch available.\n"
                food_description += "\n"

        except (KeyError, TypeError) as e:
            food_description = "Failed to parse meals."
            print("Error:", e)
    else:
        food_description = "Could not fetch the food data."

    embed = discord.Embed(description=food_description, color=discord.Color.green())
    embed.set_footer(text="Menu updated daily.")
    return embed


def build_weekly_embed():
    """Build the embed for the weekly food menu, grouping all options per day."""
    meals_by_day = get_foodWeekly()
    current_week = datetime.now().isocalendar().week
    weekly_description = f"# Week {current_week}\n\n"

    # Group courses by date so both meat and veggie appear under one heading
    grouped = {}  # date string -> {"name": weekday_name, "courses": []}
    for day in meals_by_day:
        try:
            date_str = day['date']
            date_obj = datetime.fromisoformat(date_str)
            weekday_name = date_obj.strftime('%A')
            if date_str not in grouped:
                grouped[date_str] = {"name": weekday_name, "courses": []}
            for course in day.get('courses', []):
                grouped[date_str]["courses"].append(course['name'])
        except Exception:
            pass

    for date_str, info in grouped.items():
        weekly_description += f"**{info['name']}**:\n"
        if info["courses"]:
            for course in info["courses"]:
                weekly_description += f"- {course}\n"
        else:
            weekly_description += "- No lunch available.\n"
        weekly_description += "\n"

    embed = discord.Embed(description=weekly_description, color=discord.Color.green())
    embed.set_footer(text="Menu updated weekly.")
    return embed


def setup(client: discord.Client):
    food_channel_id = int(os.getenv("FOOD_CHANNEL_ID", "0"))

    # ── Scheduled: daily at 08:00 (weekdays only) ──────────────────────────────
    @tasks.loop(time=datetime.strptime("08:00", "%H:%M").time())
    async def post_daily_food():
        if datetime.now().weekday() >= 5:  # 5 = Saturday, 6 = Sunday
            return
        channel = client.get_channel(food_channel_id)
        if channel is None:
            print(f"[food] Could not find channel {food_channel_id}")
            return
        embed = build_today_embed()
        await channel.send(content="@food-update", embed=embed, allowed_mentions=allowed_mentions)
        print(f"[food] Posted daily menu to #{channel.name}")

    # ── Scheduled: weekly on Monday at 08:00 ───────────────────────────────────
    @tasks.loop(time=datetime.strptime("08:00", "%H:%M").time())
    async def post_weekly_food():
        if datetime.now().weekday() != 0:  # 0 = Monday
            return
        channel = client.get_channel(food_channel_id)
        if channel is None:
            print(f"[food] Could not find channel {food_channel_id}")
            return
        embed = build_weekly_embed()
        await channel.send(content=f"<@&{role_id}>", embed=embed, allowed_mentions=allowed_mentions)
        print(f"[food] Posted weekly menu to #{channel.name}")

    # Start loops once bot is ready
    @client.event
    async def on_ready_food():
        if not post_daily_food.is_running():
            post_daily_food.start()
        if not post_weekly_food.is_running():
            post_weekly_food.start()

    # Wire on_ready into the client
    original_on_ready = client.event.__func__ if hasattr(client.event, '__func__') else None

    @client.listen('on_ready')
    async def food_scheduler_ready():
        if not post_daily_food.is_running():
            post_daily_food.start()
        if not post_weekly_food.is_running():
            post_weekly_food.start()
        print("[food] Scheduled food posts started.")

    # ── Slash command: /food-today ─────────────────────────────────────────────
    @client.tree.command(name="food-today", description="Get today's food menu")
    async def foodToday(interaction: discord.Interaction):
        await interaction.response.defer()
        embed = build_today_embed()
        await interaction.followup.send(content="@food-update", embed=embed, allowed_mentions=allowed_mentions)

    # ── Slash command: /food-weekly ────────────────────────────────────────────
    @client.tree.command(name="food-weekly", description="Get this week's food menu")
    async def foodWeekly(interaction: discord.Interaction):
        await interaction.response.defer()
        embed = build_weekly_embed()
        await interaction.followup.send(content=f"<@&{role_id}>", embed=embed, allowed_mentions=allowed_mentions)