import discord
from discord.ext import commands
import os
import asyncio
from dotenv import load_dotenv
from cogs.keep_alive import keep_alive
keep_alive()



load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# List your cogs here
initial_cogs = [
    "cogs.punchin",
    "cogs.attendance",
    "cogs.tasks",
]


@bot.event
async def on_ready():
    if bot.user is not None:
        print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")
    else:
        print("✅ Logged in, but bot.user is None")
    print("🔗 Bot is ready and connected to Discord!")


async def load_cogs():
    """Load all cogs with error handling"""
    for cog in initial_cogs:
        try:
            await bot.load_extension(cog)
            print(f"✅ Loaded {cog}")
        except Exception as e:
            print(f"❌ Failed to load {cog}: {e}")


async def main():
    if TOKEN is None:
        print("❌ DISCORD_TOKEN environment variable not set.")
        return
    async with bot:
        await load_cogs()
        try:
            await bot.start(TOKEN)
        except Exception as e:
            print(f"❌ Bot failed to start: {e}")


if __name__ == "__main__":
    asyncio.run(main())
