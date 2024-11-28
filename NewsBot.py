import asyncio
import discord
from discord.ext import commands
from bs4 import BeautifulSoup
import feedparser
import requests
import csv
import json
import time

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

    def has_seen_post(self, post_id):
        try:
            with open(self.post_ids_file, "r") as file:
                reader = csv.reader(file)
                for row in reader:
                    if row[0] == post_id:
                        return True
        except FileNotFoundError:
            pass
        return False

    def mark_post_as_seen(self, post_id):
        with open(self.post_ids_file, "a", newline="") as file:
            writer = csv.writer(file)
            writer.writerow([post_id])

    def get_latest_post(self):
            url = "https://www.reddit.com/user/groundnewsfeed.json"
            headers = {"User-Agent": "groundnews_feed_monitor"}
            response = requests.get(url, headers=headers)

            if response.status_code != 200:
                print(f"Failed to retrieve data. Status code: {response.status_code}")
                return None

            data = json.loads(response.text)
            posts = data["data"]["children"]

            # Calculate the threshold timestamp for posts older than 3 days
            threshold_timestamp = int(time.time()) - 259200

            for post in posts:
                if post["data"]["author"] == "groundnewsfeed":
                    post_id = post["data"]["id"]
                    title = post["data"]["title"]
                    url = post["data"]["url_overridden_by_dest"]
                    created_utc = post["data"]["created_utc"]

                    if created_utc < threshold_timestamp:
                        continue  # Skip posts older than 3 days

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

    target_channel_id = #channel id for testing
    while True:
        feed = GroundNewsFeed()
        latest_post = feed.get_latest_post()
        if latest_post:
            title, url = latest_post
            target_channel = bot.get_channel(target_channel_id)
            if target_channel:
                await target_channel.send(f"Title: {title}\nURL: {url}")
            else:
                print(f"Failed to find target channel with ID {target_channel_id}")
        await asyncio.sleep(60)  # Wait 1 minute before checking again


# Run the bot with the token
bot.run('<bot-token>')