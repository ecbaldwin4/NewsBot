import asyncio
import os
import discord
from discord.ext import commands
import csv

from dotenv import load_dotenv

load_dotenv('token.env')
DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')

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
        with open('target_channels.csv', 'r') as file:
            reader = csv.reader(file)
            for row in reader:
                guild_id, channel_id = int(row[0]), int(row[1])
                target_channels[guild_id] = channel_id
    except FileNotFoundError:
        pass

# Save target channels to CSV file
def save_target_channels():
    with open('target_channels.csv', 'w', newline='') as file:
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

async def post_news():
    await bot.wait_until_ready()
    feed = NewsFeed()
    while True:
        if target_channels:  # Check if target_channels is not empty
            for guild_id, channel_id in target_channels.items():
                guild = bot.get_guild(guild_id)
                if guild:
                    target_channel = guild.get_channel(channel_id)
                    if target_channel:
                        json_url, author = feed.get_random_source()
                        latest_post = feed.get_latest_post(json_url, author)
                        if latest_post:
                            title, url = latest_post
                            await target_channel.send(f"Title: {title}\nURL: {url}")
        await asyncio.sleep(30)  # Wait 30 seconds before checking again

@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')
    bot.loop.create_task(post_news())

# Command to make the bot say hello
@bot.command(name='hello')
async def hello(ctx):
    try:
        await ctx.send(f'Hello {ctx.author.mention}!')
    except discord.Forbidden:
        print("Bot does not have permission to send messages in this channel.")

# Run the bot with the token
async def main():
    await bot.start(DISCORD_BOT_TOKEN)

asyncio.run(main())