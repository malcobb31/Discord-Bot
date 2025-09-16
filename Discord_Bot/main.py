# main.py
import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import asyncio

# ----------------- Load Environment Variables -----------------
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")  # Your bot token in .env
GUILD_ID = os.getenv("GUILD_ID")    # Optional: restrict commands to one server (faster sync)

# ----------------- Bot Setup -----------------
intents = discord.Intents.default()
intents.message_content = True  # Required to read messages
intents.members = True          # Required for attendance, punch-in tracking

bot = commands.Bot(command_prefix="!", intents=intents)

# ----------------- Startup Event -----------------
@bot.event
async def on_ready():
    """Runs when the bot is online"""
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")
    print("------")

    try:
        # Sync slash commands
        if GUILD_ID:
            guild = discord.Object(id=int(GUILD_ID))
            bot.tree.copy_global_to(guild=guild)
            await bot.tree.sync(guild=guild)
            print(f"🔄 Synced slash commands to guild {GUILD_ID}")
        else:
            await bot.tree.sync()
            print("🔄 Synced global slash commands")

    except Exception as e:
        print(f"❌ Failed to sync commands: {e}")


# ----------------- Load Cogs -----------------
async def load_cogs():
    """Load all cogs from cogs/ folder"""
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            try:
                await bot.load_extension(f"cogs.{filename[:-3]}")
                print(f"✅ Loaded cog: {filename}")
            except Exception as e:
                print(f"❌ Failed to load cog {filename}: {e}")


# ----------------- Run Bot -----------------
async def main():
    async with bot:
        await load_cogs()
        await bot.start(TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
