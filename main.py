import asyncio
import requests
import csv
import json
import time
import os

import discord
from discord.ext import commands

from dotenv import load_dotenv

load_dotenv('token.env')
DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
CHANNEL_ID = os.getenv('CHANNEL_ID')

# Create a new bot instance with a specified command prefix
intents = discord.Intents.default()
intents.typing = False
intents.presences = False
intents.members = True  # Server Members Intent
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

class GroundNewsFeed:
    def __init__(self, post_ids_file="seen_post_ids.csv"):
        self.post_ids_file = post_ids_file
        self.seen_post_ids = self.load_seen_post_ids()

    def load_seen_post_ids(self):
        try:
            with open(self.post_ids_file, "r") as file:
                reader = csv.reader(file)
                return {row[0] for row in reader}
        except FileNotFoundError:
            return set()

    def save_seen_post_ids(self):
        with open(self.post_ids_file, "w", newline="") as file:
            writer = csv.writer(file)
            for post_id in self.seen_post_ids:
                writer.writerow([post_id])

    def has_seen_post(self, post_id):
        return post_id in self.seen_post_ids

    def mark_post_as_seen(self, post_id):
        self.seen_post_ids.add(post_id)
        self.save_seen_post_ids()

    def get_latest_post(self):
        url = "https://www.reddit.com/user/groundnewsfeed.json"
        headers = {"User-Agent": "groundnews_feed_monitor"}
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            print(f"Failed to retrieve data. Status code: {response.status_code}")
            return None

        data = json.loads(response.text)
        posts = data["data"]["children"]

        # Calculate the threshold timestamp for posts older than 24 hours
        threshold_timestamp = int(time.time()) - 86400

        for post in posts:
            if post["data"]["author"] == "groundnewsfeed":
                post_id = post["data"]["id"]
                title = post["data"]["title"]
                url = post["data"]["url_overridden_by_dest"]
                created_utc = post["data"]["created_utc"]

                if created_utc < threshold_timestamp:
                    continue  # Skip posts older than 24 hours

                if not self.has_seen_post(post_id):
                    self.mark_post_as_seen(post_id)
                    return title, url

        return None


@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')
    
    # Print the guilds (servers) the bot is in
    print('Guilds:')
    for guild in bot.guilds:
        print(f'- {guild.name} (ID: {guild.id})')
        
        # Print the text channels in each guild
        print('  Text Channels:')
        for channel in guild.text_channels:
            print(f'    - {channel.name} (ID: {channel.id})')

    target_channel_id = CHANNEL_ID
    feed = GroundNewsFeed()
    while True:
        latest_post = feed.get_latest_post()
        if latest_post:
            title, url = latest_post
            target_channel = bot.get_channel(target_channel_id)
            if target_channel:
                await target_channel.send(f"Title: {title}\nURL: {url}")
            else:
                print(f"Failed to find target channel with ID {target_channel_id}")
        await asyncio.sleep(60)  # Wait 1 minute before checking again

# Command to make the bot say hello
@bot.command(name='hello')
async def hello(ctx):
    try:
        await ctx.send(f'Hello {ctx.author.mention}!')
    except discord.Forbidden:
        print("Bot does not have permission to send messages in this channel.")

# Run the bot with the token
bot.run(DISCORD_BOT_TOKEN)
