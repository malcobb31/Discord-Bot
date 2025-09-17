import discord
from discord.ext import commands
from discord import app_commands
import json, os
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import io

ATTENDANCE_FILE = "data/attendance.json"

# ------------------------
# Utility functions
# ------------------------
def load_attendance():
    if not os.path.exists(ATTENDANCE_FILE):
        return {}
    with open(ATTENDANCE_FILE, "r") as f:
        return json.load(f)

def save_attendance(data):
    with open(ATTENDANCE_FILE, "w") as f:
        json.dump(data, f, indent=4)

# ------------------------
# Calendar Cog
# ------------------------
class Calendar(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="calendar", description="View your attendance calendar (last 30 days)")
    async def calendar(self, interaction: discord.Interaction):
        user = interaction.user
        user_id = str(user.id)

        attendance = load_attendance()

        # If no attendance logged
        if user_id not in attendance:
            await interaction.response.send_message("❌ No attendance data found.", ephemeral=True)
            return

        # Collect last 30 days
        today = datetime.now().date()
        dates = [today - timedelta(days=i) for i in range(29, -1, -1)]  # 30 days back
        statuses = [attendance[user_id].get(d.strftime("%Y-%m-%d"), 0) for d in dates]

        # ✅ Generate heatmap
        plt.figure(figsize=(10, 2))
        plt.imshow([statuses], cmap="Greens", aspect="auto")
        plt.xticks(range(len(dates)), [d.strftime("%d-%b") for d in dates], rotation=90, fontsize=6)
        plt.yticks([])
        plt.colorbar(label="Attendance (1 = Present, 0 = Absent)")
        plt.title(f"Attendance for {user.display_name} (Last 30 days)")

        # Save plot to buffer
        buf = io.BytesIO()
        plt.savefig(buf, format="png", bbox_inches="tight")
        buf.seek(0)
        plt.close()

        file = discord.File(buf, filename="calendar.png")

        embed = discord.Embed(
            title=f"📅 Attendance Calendar - {user.display_name}",
            description="Green = Present, White = Absent",
            color=discord.Color.green()
        )
        embed.set_image(url="attachment://calendar.png")

        await interaction.response.send_message(embed=embed, file=file, ephemeral=True)


async def setup(bot):
    await bot.add_cog(Calendar(bot))
