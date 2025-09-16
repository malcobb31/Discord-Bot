import discord
from discord.ext import commands
from datetime import datetime

class PunchIn(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        if message.channel.name == "task-tracker":
            now = datetime.now().strftime("%H:%M")
            punch_channel = discord.utils.get(message.guild.text_channels, name="punch-in")

            if punch_channel:
                await punch_channel.send(
                    f"🟢 {message.author.display_name} punched in at **{now}**\n"
                    f"📌 Task: {message.content}"
                )

async def setup(bot):
    await bot.add_cog(PunchIn(bot))
