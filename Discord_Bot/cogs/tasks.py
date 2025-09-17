# cogs/task.py
import discord
from discord.ext import commands
from discord import app_commands
import json, os
from datetime import datetime
from cogs.logs import log_to_channel

TASKS_FILE = "data/tasks.json"

# ------------------------
# Utility functions
# ------------------------
def load_tasks():
    if not os.path.exists(TASKS_FILE):
        return {}
    with open(TASKS_FILE, "r") as f:
        return json.load(f)

def save_tasks(tasks):
    with open(TASKS_FILE, "w") as f:
        json.dump(tasks, f, indent=4)

# ------------------------
# Edit Modal
# ------------------------
class EditTaskModal(discord.ui.Modal, title="Edit Task"):
    def __init__(self, bot, user, date, task_index, old_task, old_time):
        super().__init__()
        self.bot = bot
        self.user = user
        self.date = date
        self.task_index = task_index

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
        try:
            tasks = load_tasks()
            user_id = str(self.user.id)

            if user_id in tasks and self.date in tasks[user_id]:
                old_task = tasks[user_id][self.date][self.task_index]["task"]
                old_time = tasks[user_id][self.date][self.task_index]["time"]

                # ✅ Update JSON
                tasks[user_id][self.date][self.task_index]["task"] = str(self.task_input.value)
                tasks[user_id][self.date][self.task_index]["time"] = str(self.time_input.value)
                save_tasks(tasks)

                await interaction.response.send_message(
                    f"✅ Task updated:\n- Before: **{old_task}** ({old_time})\n- After: **{self.task_input.value}** ({self.time_input.value})",
                    ephemeral=True
                )

                if interaction.guild is not None:
                    await log_to_channel(
                        self.bot,
                        interaction.guild,
                        f"✏️ {interaction.user.display_name} edited a task:\n"
                        f"- Before: **{old_task}** ({old_time})\n"
                        f"- After: **{self.task_input.value}** ({self.time_input.value})"
                    )
            else:
                await interaction.response.send_message("❌ Failed to update task.", ephemeral=True)

        except Exception as e:
            if not interaction.response.is_done():
                await interaction.response.send_message(f"⚠️ Error: {e}", ephemeral=True)
            else:
                await interaction.followup.send(f"⚠️ Error: {e}", ephemeral=True)

# ------------------------
# Buttons + Dropdown
# ------------------------
class EditButton(discord.ui.Button):
    def __init__(self, bot, user, date, task_index, task):
        super().__init__(label="Edit", style=discord.ButtonStyle.primary, emoji="✏️")
        self.bot, self.user, self.date, self.task_index, self.task = bot, user, date, task_index, task

    async def callback(self, interaction: discord.Interaction):
        modal = EditTaskModal(self.bot, self.user, self.date, self.task_index, self.task["task"], self.task["time"])
        await interaction.response.send_modal(modal)

class DeleteButton(discord.ui.Button):
    def __init__(self, bot, user, date, task_index):
        super().__init__(label="Delete", style=discord.ButtonStyle.danger, emoji="🗑️")
        self.bot = bot
        self.user = user
        self.date = date
        self.task_index = task_index

    async def callback(self, interaction: discord.Interaction):
        try:
            tasks = load_tasks()
            user_id = str(self.user.id)

            if user_id in tasks and self.date in tasks[user_id]:
                deleted_task = tasks[user_id][self.date].pop(self.task_index)

                if not tasks[user_id][self.date]:  # remove empty date
                    del tasks[user_id][self.date]
                if not tasks[user_id]:  # remove empty user
                    del tasks[user_id]

                save_tasks(tasks)

                await interaction.response.send_message(
                    f"🗑️ Deleted task: **{deleted_task['task']}** ({deleted_task['time']})",
                    ephemeral=True
                )

                if interaction.guild is not None:
                    await log_to_channel(
                        self.bot,
                        interaction.guild,
                        f"🗑️ {interaction.user.display_name} deleted a task: "
                        f"**{deleted_task['task']}** ({deleted_task['time']})"
                    )
            else:
                await interaction.response.send_message("❌ Failed to delete task.", ephemeral=True)

        except Exception as e:
            if not interaction.response.is_done():
                await interaction.response.send_message(f"⚠️ Error: {e}", ephemeral=True)
            else:
                await interaction.followup.send(f"⚠️ Error: {e}", ephemeral=True)



class TaskDropdown(discord.ui.Select):
    def __init__(self, bot, user, date, tasks):
        self.bot, self.user, self.date, self.tasks = bot, user, date, tasks
        options = [discord.SelectOption(label=f"{i+1}. {t['task']} ({t['time']})", value=str(i))
                   for i, t in enumerate(tasks)]
        super().__init__(placeholder="Select a task...", options=options)

    async def callback(self, interaction: discord.Interaction):
        task_index = int(self.values[0])
        task = self.tasks[task_index]
        view = discord.ui.View()
        view.add_item(EditButton(self.bot, self.user, self.date, task_index, task))
        view.add_item(DeleteButton(self.bot, self.user, self.date, task_index))
        await interaction.response.send_message(
            f"✏️ Selected: **{task['task']}** ({task['time']})", view=view, ephemeral=True
        )

# ------------------------
# Cog
# ------------------------
class Task(commands.Cog):
    def __init__(self, bot): self.bot = bot

    @app_commands.command(name="task", description="View & manage your tasks")
    async def task(self, interaction: discord.Interaction):
        user, user_id = interaction.user, str(interaction.user.id)
        today = datetime.now().strftime("%Y-%m-%d")

        tasks = load_tasks()
        if user_id not in tasks or today not in tasks[user_id]:
            await interaction.response.send_message("❌ No tasks for today.", ephemeral=True)
            return

        task_list = tasks[user_id][today]
        embed = discord.Embed(title=f"{user.display_name}'s Tasks ({today})", color=discord.Color.blue())
        for i, t in enumerate(task_list, start=1):
            embed.add_field(name=f"Task {i}", value=f"{t['task']} ({t['time']})", inline=False)

        view = discord.ui.View()
        view.add_item(TaskDropdown(self.bot, user, today, task_list))
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @app_commands.command(name="task_view", description="View tasks of a user or role")
    @app_commands.describe(user="User to check", role="Role/team to check")
    async def task_view(self, interaction: discord.Interaction, user: discord.User = None, role: discord.Role = None): # type: ignore
        today = datetime.now().strftime("%Y-%m-%d")
        tasks = load_tasks()

        if user:  # single user
            user_id = str(user.id)
            if user_id not in tasks or today not in tasks[user_id]:
                await interaction.response.send_message(f"❌ No tasks for {user.display_name}.", ephemeral=True)
                return
            embed = discord.Embed(title=f"Tasks for {user.display_name} ({today})", color=discord.Color.green())
            for i, t in enumerate(tasks[user_id][today], start=1):
                embed.add_field(name=f"Task {i}", value=f"{t['task']} ({t['time']})", inline=False)
            await interaction.response.send_message(embed=embed, ephemeral=True)

        elif role:  # whole role/team
            embed = discord.Embed(title=f"Tasks for {role.name} ({today})", color=discord.Color.purple())
            found = False
            for member in role.members:
                uid = str(member.id)
                if uid in tasks and today in tasks[uid]:
                    found = True
                    task_text = "\n".join([f"- {t['task']} ({t['time']})" for t in tasks[uid][today]])
                    embed.add_field(name=member.display_name, value=task_text, inline=False)
            if not found:
                await interaction.response.send_message(f"❌ No tasks found for role {role.name}.", ephemeral=True)
                return
            await interaction.response.send_message(embed=embed, ephemeral=True)

        else:
            await interaction.response.send_message("❌ Please provide either a user or a role.", ephemeral=True)

async def setup(bot): await bot.add_cog(Task(bot))
