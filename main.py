import asyncio
import os
import discord
from discord.ext import commands
import csv
import time
import article_json_getter
from dotenv import load_dotenv

load_dotenv('.env')
DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
TARGET_CHANNELS_FILE = 'data/target_channels.csv'
POST_IDS_AND_URLS_FILE = 'data/post_ids_and_urls.csv'
SEEN_POST_IDS_FILE = 'data/seen_post_ids.csv'
SOURCES_FILE = 'data/sources.csv'

# Create a new bot instance with a specified command prefix
intents = discord.Intents.default()
intents.typing = False
intents.presences = False
intents.members = True  # Server Members Intent
intents.message_content = True

from newsfeed import NewsFeed

bot = commands.Bot(command_prefix='!', intents=intents)

# Dictionary to store the target channel for each guild
target_channels = {}

# Load target channels from CSV file
def load_target_channels():
    try:
        with open(TARGET_CHANNELS_FILE, 'r') as file:
            reader = csv.reader(file)
            for row in reader:
                guild_id, channel_id = int(row[0]), int(row[1])
                target_channels[guild_id] = channel_id
    except FileNotFoundError:
        pass

# Save target channels to CSV file
def save_target_channels():
    with open(TARGET_CHANNELS_FILE, 'w', newline='') as file:
        writer = csv.writer(file)
        for guild_id, channel_id in target_channels.items():
            writer.writerow([guild_id, channel_id])

load_target_channels()

@bot.event
async def on_guild_join(guild):
    # When the bot joins a new guild, send a message to the system channel
    system_channel = guild.system_channel
    if system_channel:
        await system_channel.send("Hello! I'm a news bot. Please use the `!setchannel` command to choose a channel for me to post news in.")

@bot.command(name='setchannel')
@commands.has_permissions(manage_guild=True)
async def setchannel(ctx, channel: discord.TextChannel):
    # Set the target channel for the current guild
    target_channels[ctx.guild.id] = channel.id
    save_target_channels()
    await ctx.send(f"Target channel set to {channel.mention}.")

@bot.command(name='getchannel')
@commands.has_permissions(manage_guild=True)
async def getchannel(ctx):
    # Get the target channel for the current guild
    target_channel_id = target_channels.get(ctx.guild.id)
    if target_channel_id:
        target_channel = ctx.guild.get_channel(target_channel_id)
        if target_channel:
            await ctx.send(f"Target channel is {target_channel.mention}.")
        else:
            await ctx.send("Target channel not found.")
    else:
        await ctx.send("No target channel set.")

# Dictionary to store the post IDs and URLs
post_ids_and_urls = {}

# Load post IDs and URLs from CSV file
def load_post_ids_and_urls():
    try:
        with open(POST_IDS_AND_URLS_FILE, 'r') as file:
            reader = csv.reader(file)
            for row in reader:
                post_id, url, timestamp = row
                post_ids_and_urls[post_id] = (url, float(timestamp))
    except FileNotFoundError:
        pass

# Save post IDs and URLs to CSV file
def save_post_ids_and_urls():
    with open(POST_IDS_AND_URLS_FILE, 'w', newline='') as file:
        writer = csv.writer(file)
        current_time = time.time()
        for post_id, (url, timestamp) in post_ids_and_urls.items():
            if current_time - timestamp < 86400:  # 86400 seconds in 24 hours
                writer.writerow([post_id, url, timestamp])

load_post_ids_and_urls()

import similarity_checker
from similarity_checker import headline_is_similar

async def post_news():
    await bot.wait_until_ready()
    feed = NewsFeed()
    while True:
        print("Checking for posts...")
        if target_channels:  
            latest_post = feed.get_latest_post_from_any_source()
            if latest_post:
                title, url = latest_post
                post_headline = headline_is_similar(title)
                if post_headline:
                    for guild_id, channel_id in target_channels.items():
                        guild = bot.get_guild(guild_id)
                        if guild:
                            target_channel = guild.get_channel(channel_id)
                            if target_channel:
                                message = await target_channel.send(f"Title: {title}\nURL: {url}")
                                post_ids_and_urls[str(message.id)] = (url, time.time())
                                save_post_ids_and_urls()
                else:
                    continue
            else:
                print("No posts found...")
        await asyncio.sleep(240)

@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')
    bot.loop.create_task(post_news())

# Command to make the bot say hello
@bot.command(name='news?')
async def hello(ctx):
    try:
        await ctx.send(f'Hello {ctx.author.mention}! I am online.')
    except discord.Forbidden:
        print("Bot does not have permission to send messages in this channel.")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if "war crime" in message.content.lower():
        await message.channel.send("It's never a war crime the first time.")
        await message.add_reaction("🇨🇦")

    await bot.process_commands(message)

# Run the bot with the token
async def main():
    await bot.start(DISCORD_BOT_TOKEN)

asyncio.run(main())