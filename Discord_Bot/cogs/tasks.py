import discord
from discord.ext import commands
import json
import os

DATA_FILE = "data/tasks.json"


class Tasks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        os.makedirs("data", exist_ok=True)
        if not os.path.exists(DATA_FILE):
            with open(DATA_FILE, "w") as f:
                json.dump({}, f)

    def load_data(self):
        with open(DATA_FILE, "r") as f:
            return json.load(f)

    def save_data(self, data):
        with open(DATA_FILE, "w") as f:
            json.dump(data, f, indent=4)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Capture tasks submitted in #task-tracker"""
        if message.author.bot:
            return
        if message.channel.name != "task-tracker":
            return

        if message.content.startswith("Task:"):
            # Split into multiple tasks
            tasks = [
                t.strip("- ").strip()
                for t in message.content.splitlines()[1:]
                if t.strip()
            ]

            if not tasks:
                return

            data = self.load_data()
            data[str(message.author.id)] = [
                {"task": t, "status": "pending"} for t in tasks
            ]
            self.save_data(data)

            # Embed display
            embed = discord.Embed(
                title=f"📝 Tasks for {message.author.display_name}",
                color=0x3498db,
            )
            for i, t in enumerate(tasks, start=1):
                embed.add_field(name=f"Task {i}", value=f"{t} (⏳ Pending)", inline=False)

            view = TaskButtons(self, message.author.id, len(tasks))
            await message.channel.send(embed=embed, view=view)

    @commands.command(name="mytask")
    async def mytask(self, ctx):
        """Show your current tasks"""
        data = self.load_data()
        tasks = data.get(str(ctx.author.id))

        if not tasks:
            await ctx.send("⚠️ You don’t have any tasks yet.")
            return

        embed = discord.Embed(
            title=f"📋 {ctx.author.display_name}'s Tasks",
            color=0x2ecc71,
        )
        for i, task in enumerate(tasks, start=1):
            status_icon = "✅" if task["status"] == "done" else (
                "❌" if task["status"] == "not done" else "⏳"
            )
            embed.add_field(
                name=f"Task {i}",
                value=f"{task['task']} ({status_icon} {task['status']})",
                inline=False,
            )
        await ctx.send(embed=embed)

    @commands.command(name="task_edit")
    async def task_edit(self, ctx, task_number: int, *, new_text: str):
        """Edit one of your tasks"""
        data = self.load_data()
        tasks = data.get(str(ctx.author.id))

        if not tasks or task_number < 1 or task_number > len(tasks):
            await ctx.send("⚠️ Invalid task number.")
            return

        tasks[task_number - 1]["task"] = new_text
        self.save_data(data)
        await ctx.send(f"✏️ Task {task_number} updated to: {new_text}")

    @commands.command(name="task_delete")
    async def task_delete(self, ctx, task_number: int):
        """Delete one of your tasks"""
        data = self.load_data()
        tasks = data.get(str(ctx.author.id))

        if not tasks or task_number < 1 or task_number > len(tasks):
            await ctx.send("⚠️ Invalid task number.")
            return

        deleted = tasks.pop(task_number - 1)
        self.save_data(data)
        await ctx.send(f"🗑️ Deleted task: {deleted['task']}")

    @commands.command(name="logs")
    @commands.has_permissions(administrator=True)
    async def logs(self, ctx):
        """Show logs of all users' tasks (Admin only)"""
        data = self.load_data()

        if not data:
            await ctx.send("📂 No tasks logged yet.")
            return

        embed = discord.Embed(title="📜 Task Logs", color=0xe67e22)

        for user_id, tasks in data.items():
            user = self.bot.get_user(int(user_id))
            name = user.display_name if user else f"User {user_id}"

            task_list = "\n".join(
                [
                    f"- {t['task']} ({t['status']})"
                    for t in tasks
                ]
            ) or "No tasks"

            embed.add_field(name=name, value=task_list, inline=False)

        await ctx.send(embed=embed)


class TaskButtons(discord.ui.View):
    def __init__(self, cog, user_id, task_count):
        super().__init__(timeout=None)
        self.cog = cog
        self.user_id = user_id
        self.task_count = task_count

        # Add ✅ and ❌ for each task
        for i in range(task_count):
            self.add_item(TaskButton(cog, user_id, i, "✅", "done"))
            self.add_item(TaskButton(cog, user_id, i, "❌", "not done"))


class TaskButton(discord.ui.Button):
    def __init__(self, cog, user_id, task_index, label, status):
        super().__init__(label=label,
                         style=discord.ButtonStyle.green if status == "done" else discord.ButtonStyle.red)
        self.cog = cog
        self.user_id = user_id
        self.task_index = task_index
        self.status = status

    async def callback(self, interaction: discord.Interaction):
        data = self.cog.load_data()
        tasks = data.get(str(self.user_id), [])

        if 0 <= self.task_index < len(tasks):
            tasks[self.task_index]["status"] = self.status
            self.cog.save_data(data)

            embed = discord.Embed(
                title=f"📝 Tasks for {interaction.user.display_name}",
                color=0x2ecc71,
            )
            for i, task in enumerate(tasks, start=1):
                status_icon = "✅" if task["status"] == "done" else (
                    "❌" if task["status"] == "not done" else "⏳"
                )
                embed.add_field(
                    name=f"Task {i}",
                    value=f"{task['task']} ({status_icon} {task['status']})",
                    inline=False,
                )

            await interaction.response.edit_message(embed=embed, view=self.view)


async def setup(bot):
    await bot.add_cog(Tasks(bot))
