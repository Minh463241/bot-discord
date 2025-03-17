import discord
from discord.ext import commands
import asyncio
from datetime import timedelta
import os
from pymongo import MongoClient

# Thiết lập intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Kết nối tới MongoDB
mongo_uri = os.getenv("MONGO_URI", "mongodb+srv://test:12341234@cluster0.i3vkq.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
client = MongoClient(mongo_uri)
db = client["discord_bot"]  # Tên database
banned_words_collection = db["banned_words"]  # Tên collection

# Lấy danh sách banned_words từ MongoDB hoặc từ biến môi trường
def load_banned_words():
    banned_words_env = os.getenv("BANNED_WORDS", "").split(",")
    banned_words_env = [word.strip() for word in banned_words_env if word.strip()]
    
    # Lấy từ MongoDB
    mongo_words = banned_words_collection.distinct("word")
    return list(set(banned_words_env + mongo_words))  # Gộp và loại bỏ trùng lặp

banned_words = load_banned_words()

@bot.event
async def on_ready():
    print(f'Bot đã sẵn sàng với tên: {bot.user}')

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    content = message.content.lower()

    for word in banned_words:
        if word in content:
            mute_duration = timedelta(minutes=15)
            try:
                await message.author.timeout(mute_duration, reason=f"Sử dụng từ khóa cấm: {word}")
                await message.channel.send(
                    f"{message.author.mention} đã bị mute 15 phút vì sử dụng từ khóa cấm: '{word}'"
                )
                await message.delete()
            except discord.Forbidden:
                await message.channel.send("Bot không có đủ quyền để mute người dùng này!")
            except Exception as e:
                await message.channel.send(f"Có lỗi xảy ra: {e}")
            return

    await bot.process_commands(message)

@bot.command()
@commands.has_permissions(administrator=True)
async def add(ctx, *, word):
    word = word.lower()
    if word not in banned_words:
        # Thêm vào MongoDB
        banned_words_collection.update_one(
            {"word": word},
            {"$set": {"word": word}},
            upsert=True
        )
        banned_words.append(word)  # Cập nhật danh sách trong bộ nhớ
        await ctx.send(f"Đã thêm từ '{word}' vào danh sách từ khóa cấm.")
    else:
        await ctx.send(f"Từ '{word}' đã có trong danh sách từ khóa cấm.")

# Chạy bot với token
bot.run(os.getenv("BOT_DISCORD_TOKEN"))