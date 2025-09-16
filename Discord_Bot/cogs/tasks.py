# cogs/tasks.py
import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from datetime import datetime

# Path to store tasks in JSON
TASKS_FILE = "data/tasks.json"


# ----------------- Utility Functions -----------------
def load_tasks():
    """Load tasks from the JSON file"""
    if not os.path.exists(TASKS_FILE):
        return {}
    with open(TASKS_FILE, "r") as f:
        return json.load(f)


def save_tasks(tasks):
    """Save tasks to the JSON file"""
    with open(TASKS_FILE, "w") as f:
        json.dump(tasks, f, indent=4)


# ----------------- Tasks Cog -----------------
class Tasks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ----------------- /mytasks -----------------
    @app_commands.command(name="mytasks", description="View and manage your tasks for today")
    async def mytasks(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        today = str(datetime.now().date())

        tasks = load_tasks()
        user_tasks = tasks.get(user_id, {}).get(today, [])

        if not user_tasks:
            await interaction.response.send_message("❌ You don't have any tasks for today.", ephemeral=True)
            return

        # Create embed
        embed = discord.Embed(
            title=f"{interaction.user.name}'s Tasks ({today})",
            color=discord.Color.blue()
        )
        for idx, task in enumerate(user_tasks, start=1):
            embed.add_field(
                name=f"Task {idx}",
                value=f"📝 {task['task']}  ⏱ {task['duration']}",
                inline=False
            )

        # Buttons for Edit/Delete
        view = TaskButtons(user_id, today)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    # ----------------- /task (Admin only) -----------------
    @app_commands.command(name="task", description="(Admin) View a user's tasks for a given date")
    @app_commands.describe(user="The user to check", date="Date in YYYY-MM-DD format (optional)")
    async def task(self, interaction: discord.Interaction, user: discord.Member, date: str = None):
        # Admin check
        member = interaction.user
        # If interaction.user is not a Member, fetch from guild
        if not isinstance(member, discord.Member):
            if interaction.guild is not None:
                member = interaction.guild.get_member(interaction.user.id)
            else:
                member = None
        if not member or not member.guild_permissions.administrator:
            await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
            return

        user_id = str(user.id)
        if date:
            try:
                date_obj = datetime.strptime(date, "%Y-%m-%d").date()
            except ValueError:
                await interaction.response.send_message("❌ Invalid date format. Use YYYY-MM-DD.", ephemeral=True)
                return
        else:
            date_obj = datetime.now().date()

        date_str = str(date_obj)
        tasks = load_tasks()
        user_tasks = tasks.get(user_id, {}).get(date_str, [])

        if not user_tasks:
            await interaction.response.send_message(f"❌ {user.name} has no tasks on {date_str}.", ephemeral=True)
            return

        # Create embed
        embed = discord.Embed(
            title=f"{user.name}'s Tasks ({date_str})",
            color=discord.Color.green()
        )
        for idx, task in enumerate(user_tasks, start=1):
            embed.add_field(
                name=f"Task {idx}",
                value=f"📝 {task['task']}  ⏱ {task['duration']}",
                inline=False
            )

        await interaction.response.send_message(embed=embed, ephemeral=True)


# ----------------- Buttons for Editing -----------------
class TaskButtons(discord.ui.View):
    def __init__(self, user_id, date):
        super().__init__(timeout=60)  # buttons expire after 60s
        self.user_id = user_id
        self.date = date

    @discord.ui.button(label="✏️ Edit Task", style=discord.ButtonStyle.primary)
    async def edit_task(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("⚡ Edit task feature coming soon!", ephemeral=True)

    @discord.ui.button(label="🗑 Delete Task", style=discord.ButtonStyle.danger)
    async def delete_task(self, interaction: discord.Interaction, button: discord.ui.Button):
        tasks = load_tasks()

        if self.user_id in tasks and self.date in tasks[self.user_id]:
            del tasks[self.user_id][self.date]
            save_tasks(tasks)
            await interaction.response.send_message("🗑 All tasks for today deleted!", ephemeral=True)
        else:
            await interaction.response.send_message("❌ No tasks found to delete.", ephemeral=True)


# ----------------- Setup Function -----------------
async def setup(bot):
    await bot.add_cog(Tasks(bot))
