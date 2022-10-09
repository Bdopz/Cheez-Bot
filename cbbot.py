from operator import truediv
from time import sleep
import discord
from discord.ext import commands
import asyncio
import youtube_dl
import threading

token = "OTIyNjczNDE0OTk1NTgzMDA3.G-6cNg.xqa5JoOzRJjwTmKrnsdw6I3M1CJtEB6CoDG7n8"
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.voice_states = True
bot = commands.Bot(command_prefix = '?', intents = intents)

voice_clients = {}
yt_dl_opts = {'format': 'bestaudio/best'}
ytdl = youtube_dl.YoutubeDL(yt_dl_opts)

ffmpeg_options = {'options': "-vn"}

songQueues = {}

# Returns print to console to confirm a successful boot
@bot.event
async def on_ready():
    print(f"Bot logged in as {bot.user}")

async def queryQueue(ctx, guild):
    if len(songQueues[guild]) > 0:
        data = songQueues[guild][0]
        song = data['url']
        player = discord.FFmpegOpusAudio(song, **ffmpeg_options)
        voice_clients[ctx.guild.id].play(player)
        songQueues[guild].remove(data)
        await ctx.send("Now playing: " + data['title'])
        await asyncio.sleep(data['duration'] + 1)
        if ctx.voice_client.is_playing() == True: return
        await queryQueue(ctx, guild)
    else:
        if ctx.voice_client.is_playing() == False:
            await ctx.send("Queue is empty")

@bot.command()
async def play(ctx, song = None):
    guild = ctx.guild.id

    if song is None:
        return await ctx.send("huh?")

    if not("youtube.com/watch?" in song or "youtu.be/" in song):
        return await ctx.send("youtube urls only")

    if ctx.voice_client is None:
        voice_client = await ctx.author.voice.channel.connect()
        voice_clients[voice_client.guild.id] = voice_client

    if not(guild in songQueues):
        songQueues[guild] = []

    loop = asyncio.get_event_loop()
    data = await loop.run_in_executor(None, lambda: ytdl.extract_info(song, download=False))
    song = data['url']

    if ctx.voice_client.is_playing() == False:
        player = discord.FFmpegOpusAudio(song, **ffmpeg_options)
        await ctx.send("Now playing: " + data['title'])
        voice_clients[ctx.guild.id].play(player)
        await asyncio.sleep(data['duration'] + 1)
        if ctx.voice_client.is_playing() == True: return
        await queryQueue(ctx, guild)
    else:
        songQueues[guild].append(data)
        await ctx.send("Now in queue: " + data['title'])

@bot.command()
async def skip(ctx):
    if ctx.voice_client is not None:
        voice_clients[ctx.guild.id].stop()
        await queryQueue(ctx, ctx.guild.id)

@bot.command()
async def leave(ctx):
    if ctx.voice_client is not None:
        voice_clients[ctx.guild.id].disconnect()
        songQueues[ctx.guild.id].clear()

bot.run(token)