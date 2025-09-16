# cogs/logs.py
import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from datetime import datetime

TASKS_FILE = "data/tasks.json"
ATTENDANCE_FILE = "data/attendance.json"


# ----------------- Utility Functions -----------------
def load_json(path):
    """Load JSON file safely"""
    if not os.path.exists(path):
        return {}
    with open(path, "r") as f:
        return json.load(f)


# ----------------- Logs Cog -----------------
class Logs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ----------------- /logs -----------------
    @app_commands.command(name="logs", description="View bot logs (Admins only)")
    @app_commands.checks.has_permissions(administrator=True)
    async def logs(self, interaction: discord.Interaction):
        tasks_data = load_json(TASKS_FILE)
        attendance_data = load_json(ATTENDANCE_FILE)

        embed = discord.Embed(
            title="📜 Bot Logs",
            description="Here are the latest activity logs.",
            color=discord.Color.gold(),
            timestamp=datetime.now()
        )

        # Add task logs
        if tasks_data:
            recent_tasks = []
            for user_id, task_list in tasks_data.items():
                user = interaction.guild.get_member(int(user_id))
                username = user.display_name if user else f"User({user_id})"
                for task in task_list:
                    recent_tasks.append(f"📝 {username}: {task['task']} ({task['duration']}) on {task['date']}")
            embed.add_field(
                name="📝 Tasks",
                value="\n".join(recent_tasks[-5:]) if recent_tasks else "No tasks logged.",
                inline=False
            )
        else:
            embed.add_field(name="📝 Tasks", value="No tasks logged.", inline=False)

        # Add attendance logs
        if attendance_data:
            recent_attendance = []
            for user_id, dates in attendance_data.items():
                user = interaction.guild.get_member(int(user_id))
                username = user.display_name if user else f"User({user_id})"
                for date, status in dates.items():
                    recent_attendance.append(f"📅 {username}: {status} on {date}")
            embed.add_field(
                name="📅 Attendance",
                value="\n".join(recent_attendance[-5:]) if recent_attendance else "No attendance logged.",
                inline=False
            )
        else:
            embed.add_field(name="📅 Attendance", value="No attendance logged.", inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)


# ----------------- Setup Function -----------------
async def setup(bot):
    await bot.add_cog(Logs(bot))
