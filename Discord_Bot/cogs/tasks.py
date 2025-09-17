import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from datetime import datetime

TASKS_FILE = "data/tasks.json"

# ------------------------
# Utility functions
# ------------------------
def load_tasks():
    """Load tasks.json file into memory"""
    if not os.path.exists(TASKS_FILE):
        return {}
    with open(TASKS_FILE, "r") as f:
        return json.load(f)

def save_tasks(tasks):
    """Save updated tasks back to tasks.json"""
    with open(TASKS_FILE, "w") as f:
        json.dump(tasks, f, indent=4)


# ------------------------
# Modal for editing tasks
# ------------------------
class EditTaskModal(discord.ui.Modal, title="Edit Task"):
    def __init__(self, user_id, date, task_index, old_task, old_time):
        super().__init__()
        self.user_id = str(user_id)
        self.date = date
        self.task_index = task_index

        # Pre-fill task + time
        self.task_input = discord.ui.TextInput(
            label="Task",
            default=old_task,
            required=True,
            style=discord.TextStyle.long
        )
        self.time_input = discord.ui.TextInput(
            label="Time Duration",
            default=old_time,
            required=True,
            style=discord.TextStyle.short
        )

        self.add_item(self.task_input)
        self.add_item(self.time_input)

    async def on_submit(self, interaction: discord.Interaction):
        tasks = load_tasks()
        if self.user_id in tasks and self.date in tasks[self.user_id]:
            tasks[self.user_id][self.date][self.task_index]["task"] = str(self.task_input.value)
            tasks[self.user_id][self.date][self.task_index]["time"] = str(self.time_input.value)
            save_tasks(tasks)
            await interaction.response.send_message(
                f"✅ Task updated to: **{self.task_input.value}** ({self.time_input.value})",
                ephemeral=True
            )
        else:
            await interaction.response.send_message("❌ Failed to update task.", ephemeral=True)


# ------------------------
# Delete Button
# ------------------------
class DeleteButton(discord.ui.Button):
    def __init__(self, user_id, date, task_index):
        super().__init__(label="Delete", style=discord.ButtonStyle.danger, emoji="🗑️")
        self.user_id = user_id
        self.date = date
        self.task_index = task_index

    async def callback(self, interaction: discord.Interaction):
        tasks = load_tasks()
        if self.user_id in tasks and self.date in tasks[self.user_id]:
            deleted_task = tasks[self.user_id][self.date].pop(self.task_index)
            if not tasks[self.user_id][self.date]:  # remove empty date
                del tasks[self.user_id][self.date]
            if not tasks[self.user_id]:  # remove empty user
                del tasks[self.user_id]

            save_tasks(tasks)

            await interaction.response.send_message(
                f"🗑️ Deleted task: **{deleted_task['task']}** ({deleted_task['time']})",
                ephemeral=True
            )
        else:
            await interaction.response.send_message("❌ Failed to delete task.", ephemeral=True)


# ------------------------
# Dropdown for task selection
# ------------------------
class TaskDropdown(discord.ui.Select):
    def __init__(self, user_id, date, tasks):
        self.user_id = user_id
        self.date = date
        self.tasks = tasks

        # Generate dropdown options
        options = [
            discord.SelectOption(
                label=f"{i+1}. {task['task']} ({task['time']})",
                value=str(i)
            )
            for i, task in enumerate(tasks)
        ]

        super().__init__(
            placeholder="Select a task to edit or delete...",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        task_index = int(self.values[0])
        task = self.tasks[task_index]

        view = discord.ui.View()
        view.add_item(EditButton(self.user_id, self.date, task_index, task))
        view.add_item(DeleteButton(self.user_id, self.date, task_index))

        await interaction.response.send_message(
            f"✏️ You selected: **{task['task']}** ({task['time']})",
            view=view,
            ephemeral=True
        )


# ------------------------
# Edit Button (opens modal)
# ------------------------
class EditButton(discord.ui.Button):
    def __init__(self, user_id, date, task_index, task):
        super().__init__(label="Edit", style=discord.ButtonStyle.primary, emoji="✏️")
        self.user_id = user_id
        self.date = date
        self.task_index = task_index
        self.task = task

    async def callback(self, interaction: discord.Interaction):
        modal = EditTaskModal(
            self.user_id,
            self.date,
            self.task_index,
            self.task["task"],
            self.task["time"]
        )
        await interaction.response.send_modal(modal)


# ------------------------
# Cog for MyTasks command
# ------------------------
class MyTasks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="mytasks", description="View and manage your tasks")
    async def mytasks(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        today = datetime.now().strftime("%Y-%m-%d")

        tasks = load_tasks()
        if user_id not in tasks or today not in tasks[user_id]:
            await interaction.response.send_message("❌ You have no tasks for today.", ephemeral=True)
            return

        task_list = tasks[user_id][today]

        embed = discord.Embed(
            title=f"{interaction.user.display_name}'s Tasks ({today})",
            color=discord.Color.blue()
        )
        for i, t in enumerate(task_list, start=1):
            embed.add_field(name=f"Task {i}", value=f"{t['task']} ({t['time']})", inline=False)

        view = discord.ui.View()
        view.add_item(TaskDropdown(user_id, today, task_list))

        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


async def setup(bot):
    await bot.add_cog(MyTasks(bot))
