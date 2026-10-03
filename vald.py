import os
import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

TOKEN = os.getenv('TOKEN')
bot.run(TOKEN)
import os
from flask import Flask
from threading import Thread
import discord
from discord.ext import commands

# 1. إنشاء سيرفر وهمي لتجاوز مشكلة البورتات في Render
app = Flask('')

@app.route('/')
def home():
    return "I am alive!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# 2. إعدادات بوت الديسكورد العادية
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

# تشغيل السيرفر الوهمي أولاً ثم تشغيل البوت
keep_alive()
TOKEN = os.getenv('TOKEN')
bot.run(TOKEN)
