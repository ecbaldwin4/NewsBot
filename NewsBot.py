import asyncio
import requests
import csv
import json
import time
import os
import random

import discord
from discord.ext import commands

from dotenv import load_dotenv

load_dotenv('token.env')
DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')

# Create a new bot instance with a specified command prefix
intents = discord.Intents.default()
intents.typing = False
intents.presences = False
intents.members = True  # Server Members Intent
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

class NewsFeed:
    def __init__(self, post_ids_file="seen_post_ids.csv", sources_file="sources.csv"):
        self.post_ids_file = post_ids_file
        self.sources_file = sources_file
        self.seen_post_ids = self.load_seen_post_ids()
        self.sources = self.load_sources()

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

    def load_sources(self):
        sources = {}
        with open(self.sources_file, "r") as file:
            reader = csv.reader(file)
            next(reader)  # Skip header row
            for row in reader:
                author, json_url = row
                sources[json_url] = author
        return sources

    def get_random_source(self):
        return random.choice(list(self.sources.items()))

    def get_latest_post(self, json_url, author):
        headers = {"User-Agent": "news_feed_monitor"}
        response = requests.get(json_url, headers=headers)

        if response.status_code != 200:
            print(f"Failed to retrieve data. Status code: {response.status_code}")
            return None

        data = json.loads(response.text)
        posts = data["data"]["children"]

        # Calculate the threshold timestamp for posts older than 24 hours
        threshold_timestamp = int(time.time()) - 86400

        for post in posts:
            post_id = post["data"]["id"]
            title = post["data"]["title"]
            url = post["data"]["url_overridden_by_dest"]
            created_utc = post["data"]["created_utc"]
            post_author = post["data"]["author"]

            if created_utc < threshold_timestamp:
                continue  # Skip posts older than 24 hours

            if author == "any" or post_author == author:
                if not self.has_seen_post(post_id):
                    self.mark_post_as_seen(post_id)
                    return title, url

        return None


@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')


@bot.command(name='startnews')
async def startnews(ctx):
    feed = NewsFeed()
    while True:
        json_url, author = feed.get_random_source()
        latest_post = feed.get_latest_post(json_url, author)
        if latest_post:
            title, url = latest_post
            await ctx.send(f"Title: {title}\nURL: {url}")
        await asyncio.sleep(300)  # Wait 5 minutes before checking again


# Command to make the bot say hello
@bot.command(name='hello')
async def hello(ctx):
    try:
        await ctx.send(f'Hello {ctx.author.mention}!')
    except discord.Forbidden:
        print("Bot does not have permission to send messages in this channel.")


# Run the bot with the token
bot.run(DISCORD_BOT_TOKEN)