import os
from flask import Flask
from threading import Thread
import discord
from discord.ext import commands

# 1. إنشاء سيرفر فلاسك وقراءة البورت من Render تلقائياً
app = Flask('')

@app.route('/')
def home():
    return "I am alive!"

def run():
    # استخدام البورت الذي يحدده Render أو القيمة 8080 افتراضياً
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

# 2. إعدادات بوت الديسكورد
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

# تشغيل السيرفر ثم البوت
keep_alive()
TOKEN = os.getenv('TOKEN')
bot.run(TOKEN)
