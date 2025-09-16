import discord
from discord.ext import commands
import json
import os
from datetime import datetime, timedelta
import matplotlib.pyplot as plt

DATA_FILE = "data/attendance.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

class Attendance(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="attendance")
    async def attendance(self, ctx, member: discord.Member = None):
        """Show attendance heatmap for a user"""
        if member is None:
            member = ctx.author

        data = load_data()
        user_id = str(member.id)

        if user_id not in data:
            await ctx.send(f"❌ No attendance records found for {member.display_name}.")
            return

        # Generate heatmap
        records = data[user_id]
        start_date = datetime.now() - timedelta(days=30)
        dates = [start_date + timedelta(days=i) for i in range(31)]

        colors = []
        for d in dates:
            date_str = d.strftime("%Y-%m-%d")
            if d.weekday() in [5, 6]:  # Sat/Sun = weekend
                colors.append("lightgrey")
            elif date_str in records:
                status = records[date_str]["status"]
                if status == "Present":
                    colors.append("green")
                elif status == "Half-Day":
                    colors.append("yellow")
                else:
                    colors.append("red")
            else:
                colors.append("red")  # default Absent

        # Plot GitHub-like grid
        fig, ax = plt.subplots(figsize=(8, 2))
        ax.imshow([colors], aspect="auto")

        ax.set_xticks(range(len(dates)))
        ax.set_xticklabels([d.strftime("%d") for d in dates], rotation=90, fontsize=6)
        ax.set_yticks([])
        ax.set_title(f"Attendance for {member.display_name} (Last 30 Days)", fontsize=10)

        plt.tight_layout()
        filename = f"data/{user_id}_attendance.png"
        plt.savefig(filename)
        plt.close()

        await ctx.send(file=discord.File(filename))

async def setup(bot):
    await bot.add_cog(Attendance(bot))
