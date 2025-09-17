# cogs/tasks.py
import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from datetime import datetime

TASKS_FILE = "data/tasks.json"
LOG_CHANNEL_ID = 123456789012345678  # 🔹 Replace with your logs channel ID


# ----------------- Utility Functions -----------------
def load_json(path):
    """Load JSON file safely"""
    if not os.path.exists(path):
        return {}
    with open(path, "r") as f:
        return json.load(f)


def save_json(path, data):
    """Save JSON file safely"""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=4)


def valid_task_format(text: str) -> bool:
    """Check if a line contains duration like '2hr', '2-3hrs', '30min' etc."""
    keywords = ["hr", "hrs", "hour", "hours", "min", "mins", "minute", "minutes"]
    return any(k in text.lower() for k in keywords)


# ----------------- Tasks Cog -----------------
class Tasks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ----------------- Task Submission -----------------
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Capture tasks when user posts in #task-tracker"""
        if message.author.bot:
            return

        if not message.content.startswith("Task:") and not message.content[0].isdigit():
            return  # Ignore irrelevant messages

        user_id = str(message.author.id)
        today = datetime.today().strftime("%Y-%m-%d")

        tasks_data = load_json(TASKS_FILE)

        # Prevent multiple submissions in one day
        if user_id in tasks_data and today in tasks_data[user_id]:
            await message.channel.send(f"⚠️ {message.author.mention}, you have already submitted tasks for today.")
            return

        # Parse tasks
        lines = [line.strip() for line in message.content.split("\n") if line.strip()]
        parsed_tasks = []

        for line in lines:
            if line.lower().startswith("task:"):
                continue  # skip header
            if not valid_task_format(line):
                await message.channel.send(f"❌ Invalid format in: `{line}`. Please include duration (e.g., 2hrs, 30min).")
                return
            parsed_tasks.append(line)

        if not parsed_tasks:
            return

        # Store tasks
        if user_id not in tasks_data:
            tasks_data[user_id] = {}
        tasks_data[user_id][today] = parsed_tasks
        save_json(TASKS_FILE, tasks_data)

        # Log to punch-in channel
        punch_channel = None
        if message.guild is not None:
            punch_channel = discord.utils.get(message.guild.text_channels, name="punch-in")
        if punch_channel:
            embed = discord.Embed(
                title="✅ Punch-In Recorded",
                description="\n".join(parsed_tasks),
                color=discord.Color.green(),
                timestamp=datetime.now()
            )
            embed.set_author(name=message.author.display_name, icon_url=message.author.display_avatar.url)
            embed.set_footer(text="Fapps Bot - Task Tracker")
            await punch_channel.send(embed=embed)

        # Log to bot logs
        log_channel = self.bot.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            await log_channel.send(f"📝 {message.author.display_name} submitted tasks for {today}")

    # ----------------- /mytasks -----------------
    @app_commands.command(name="mytasks", description="View your tasks for today")
    async def mytasks(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        today = datetime.today().strftime("%Y-%m-%d")
        tasks_data = load_json(TASKS_FILE)

        if user_id not in tasks_data or today not in tasks_data[user_id]:
            await interaction.response.send_message("❌ You have not submitted any tasks today.", ephemeral=True)
            return

        embed = discord.Embed(
            title=f"📌 Your Tasks for {today}",
            description="\n".join(tasks_data[user_id][today]),
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ----------------- /task (Admin) -----------------
    @app_commands.command(name="task", description="View tasks for a user (Admin only)")
    @app_commands.checks.has_permissions(administrator=True)
    async def task(self, interaction: discord.Interaction, user: discord.Member, date: str = ""):
        date = date or datetime.today().strftime("%Y-%m-%d")
        tasks_data = load_json(TASKS_FILE)

        if str(user.id) not in tasks_data or date not in tasks_data[str(user.id)]:
            await interaction.response.send_message(f"❌ No tasks found for {user.display_name} on {date}", ephemeral=True)
            return

        embed = discord.Embed(
            title=f"📌 Tasks for {user.display_name} ({date})",
            description="\n".join(tasks_data[str(user.id)][date]),
            color=discord.Color.orange()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


# ----------------- Setup Function -----------------
async def setup(bot):
    await bot.add_cog(Tasks(bot))
