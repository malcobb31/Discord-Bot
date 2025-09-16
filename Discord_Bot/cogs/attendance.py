# cogs/attendance.py
import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import typing

ATTENDANCE_FILE = "data/attendance.json"


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


# ----------------- Attendance Cog -----------------
class Attendance(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ----------------- /attendance (user summary) -----------------
    @app_commands.command(name="attendance", description="Check attendance for a user")
    async def attendance(self, interaction: discord.Interaction, user: typing.Optional[discord.Member] = None):
        if user is None:
            if interaction.guild is not None:
                user = interaction.guild.get_member(interaction.user.id)
            else:
                user = None

        if user is None:
            await interaction.response.send_message("❌ Could not find the user.", ephemeral=True)
            return

        data = load_json(ATTENDANCE_FILE)

        user_data = data.get(str(user.id), {})
        present = sum(1 for s in user_data.values() if s == "Present")
        half_day = sum(1 for s in user_data.values() if s == "Half-Day")
        absent = sum(1 for s in user_data.values() if s == "Absent")

        embed = discord.Embed(
            title=f"📅 Attendance Summary for {user.display_name}",
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
        embed.add_field(name="✅ Present", value=str(present))
        embed.add_field(name="🌓 Half-Day", value=str(half_day))
        embed.add_field(name="❌ Absent", value=str(absent))

        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ----------------- /attendance team -----------------
    @app_commands.command(name="attendance_team", description="Check attendance summary for a team (role-based)")
    async def attendance_team(self, interaction: discord.Interaction, role: discord.Role):
        data = load_json(ATTENDANCE_FILE)

        team_summary = {"Present": 0, "Half-Day": 0, "Absent": 0}
        for member in role.members:
            user_data = data.get(str(member.id), {})
            team_summary["Present"] += sum(1 for s in user_data.values() if s == "Present")
            team_summary["Half-Day"] += sum(1 for s in user_data.values() if s == "Half-Day")
            team_summary["Absent"] += sum(1 for s in user_data.values() if s == "Absent")

        embed = discord.Embed(
            title=f"👥 Team Attendance Summary ({role.name})",
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        for status, count in team_summary.items():
            embed.add_field(name=status, value=str(count))

        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ----------------- /attendance edit -----------------
    @app_commands.command(name="attendance_edit", description="Edit attendance for a user (Admins only)")
    @app_commands.checks.has_permissions(administrator=True)
    async def attendance_edit(self, interaction: discord.Interaction, user: discord.Member, date: str, status: str):
        """Admin correction: date format YYYY-MM-DD, status = Present / Half-Day / Absent"""
        data = load_json(ATTENDANCE_FILE)

        if status not in ["Present", "Half-Day", "Absent"]:
            await interaction.response.send_message("❌ Invalid status. Use Present, Half-Day, or Absent.", ephemeral=True)
            return

        if str(user.id) not in data:
            data[str(user.id)] = {}

        data[str(user.id)][date] = status
        save_json(ATTENDANCE_FILE, data)

        await interaction.response.send_message(f"✅ Updated {user.display_name}'s attendance on {date} to {status}", ephemeral=True)

    # ----------------- /calendar -----------------
    async def calendar(self, interaction: discord.Interaction, user: typing.Optional[discord.Member] = None):
        if user is None:
            if interaction.guild is not None:
                user = interaction.guild.get_member(interaction.user.id)
            else:
                user = None
        data = load_json(ATTENDANCE_FILE)

        if user is None:
            await interaction.response.send_message("❌ Could not find the user.", ephemeral=True)
            return

        user_data = data.get(str(user.id), {})

        if not user_data:
            await interaction.response.send_message(f"❌ No attendance records found for {user.display_name}.", ephemeral=True)
            return

        # Prepare data for last 30 days
        today = datetime.today()
        dates = [today - timedelta(days=i) for i in range(30)]
        dates.reverse()

        values = []
        for d in dates:
            date_str = d.strftime("%Y-%m-%d")
            status = user_data.get(date_str, "Absent")
            if status == "Present":
                values.append(2)
            elif status == "Half-Day":
                values.append(1)
            else:
                values.append(0)

        # Plot heatmap (line-based for simplicity)
        plt.figure(figsize=(10, 2))
        date_nums = mdates.date2num(dates)
        plt.plot(date_nums, values, marker="o")
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%d-%b"))
        plt.gca().xaxis.set_major_locator(mdates.DayLocator())
        plt.yticks([0, 1, 2], ["Absent", "Half-Day", "Present"])
        plt.title(f"Attendance Heatmap - {user.display_name}")
        plt.grid(True)

        # Save and send
        filename = f"data/{user.id}_calendar.png"
        os.makedirs("data", exist_ok=True)
        plt.savefig(filename)
        plt.close()

        file = discord.File(filename, filename="calendar.png")
        await interaction.response.send_message(
            content=f"📊 Attendance calendar for {user.display_name}",
            file=file,
            ephemeral=True
        )


# ----------------- Setup Function -----------------
async def setup(bot):
    await bot.add_cog(Attendance(bot))
