# cogs/punchin.py
import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, time
import json
import os

# Path to attendance storage
ATTENDANCE_FILE = "data/attendance.json"

# ----------------- Utility Functions -----------------
def load_attendance():
    """Load attendance from JSON"""
    if not os.path.exists(ATTENDANCE_FILE):
        return {}
    with open(ATTENDANCE_FILE, "r") as f:
        return json.load(f)


def save_attendance(data):
    """Save attendance to JSON"""
    with open(ATTENDANCE_FILE, "w") as f:
        json.dump(data, f, indent=4)


def is_within_timeframe():
    """Check if current time is within 9:30 - 10:30"""
    now = datetime.now().time()
    start = time(9, 30)
    end = time(10, 30)
    return start <= now <= end


# ----------------- Punch-in Cog -----------------
class PunchIn(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ----------------- /punch-in -----------------
    @app_commands.command(name="punch_in", description="Manually punch in (only between 9:30–10:30)")
    async def punch_in(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        today = str(datetime.now().date())
        data = load_attendance()

        if not is_within_timeframe():
            await interaction.response.send_message(
                "❌ Punch-in is only allowed between **09:30–10:30 AM**.",
                ephemeral=True
            )
            return

        # Check if already punched in
        if user_id in data and today in data[user_id]:
            await interaction.response.send_message("✅ You have already punched in today.", ephemeral=True)
            return

        # Record punch-in
        data.setdefault(user_id, {})[today] = "Present"
        save_attendance(data)

        # Log punch-in to logs channel
        logs_channel = None
        if interaction.guild is not None:
            logs_channel = discord.utils.get(interaction.guild.text_channels, name="fapps-bot-logs")
        if logs_channel:
            await logs_channel.send(f"🟢 {interaction.user.mention} punched in at {datetime.now().strftime('%H:%M:%S')}")

        await interaction.response.send_message("✅ Punch-in recorded successfully!", ephemeral=True)


# ----------------- Setup Function -----------------
async def setup(bot):
    await bot.add_cog(PunchIn(bot))
