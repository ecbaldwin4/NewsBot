import asyncio
import os
import discord
from discord.ext import commands
import csv
import article_json_getter
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

# Dictionary to store the post IDs and URLs
post_ids_and_urls = {}

# Load post IDs and URLs from CSV file
def load_post_ids_and_urls():
    try:
        with open('post_ids_and_urls.csv', 'r') as file:
            reader = csv.reader(file)
            for row in reader:
                post_id, url = row
                post_ids_and_urls[post_id] = url
    except FileNotFoundError:
        pass

# Save post IDs and URLs to CSV file
def save_post_ids_and_urls():
    with open('post_ids_and_urls.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        for post_id, url in post_ids_and_urls.items():
            writer.writerow([post_id, url])

load_post_ids_and_urls()

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
                        print(json_url, author)
                        latest_post = feed.get_latest_post(json_url, author)
                        if latest_post:
                            title, url = latest_post
                            message = await target_channel.send(f"Title: {title}\nURL: {url}")
                            post_ids_and_urls[str(message.id)] = url
                            save_post_ids_and_urls()
        await asyncio.sleep(300)  # Wait 300 seconds before checking again

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


""" #### THIS FUNCTION IS FOR FUTURE AI IMPLEMENTATION. 
NOTE
WHEN A NEW POST IS SEEN AND POSTED IN DISCORD, POST_IDS_AND_URLS.CSV TAKE THE DISCORD BOT'S POST ID AND ASSOCIATES WITH THE URL IT POSTED.
LATER, IF SOMEONE REPLIES TO THE POST, THE URL CAN BE USED ALONG WITH THE JSON ARTICLE TEXT GETTER FUNCTION TO PROVIDE THE TEXT OF THE ARTICLE TO AN AI. 
THE AI CAN THEN PROVIDE A SUMMARY OF THE ARTICLE. THIS SUMMARY CAN BE USED FOR JUST SUMMARIZATION, OR THE SUMMARIZATION CAN BE STORED FOR CHAT LOGS FOR A FUTURE "DEBATEBOT"

@bot.event
async def on_message(message):
    # Check if the message is a reply to one of the bot's posts
    if message.reference and message.reference.resolved.author == bot.user:
        post_id = str(message.reference.resolved.id)
        # Check if the post ID is in the post_ids_and_urls dictionary
        if post_id in post_ids_and_urls:
            url = post_ids_and_urls[post_id]
            
            # Call the get_article_text function from article_json_getter.py
            from article_json_getter import get_article_text_from_json
            article_text_result = get_article_text_from_json(url)
            print(article_text_result)
            await message.reply(article_text_result)
    
    # Call the on_message event from the commands extension
    await bot.process_commands(message)
""" 

# Run the bot with the token
async def main():
    await bot.start(DISCORD_BOT_TOKEN)

asyncio.run(main())