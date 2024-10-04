from nextcord.ext.commands import Bot, Cog
from nextcord.ext import application_checks
from nextcord import (
    slash_command,
    Embed,
    Color,
    Interaction,
    TextChannel,
    Message,
    SlashOption,
    CategoryChannel,
    PermissionOverwrite
)

from config import EMBED_COLOR
from utils.views import HelpPanel, Confirm
from utils.functions import get_constant_id
from utils.db import DB

class Moderation(Cog):
    def __init__(self, client: Bot) -> None:
        self.client = client


    async def connect_db(self):
        self.db = DB()
        await self.db.load_db("main.db")


    @Cog.listener()
    async def on_ready(self):
        await self.connect_db()
        self.client.add_view(HelpPanel(client=self.client))
        return


    @slash_command(name="subject")
    async def subject(self, interaction: Interaction):
        return


    @application_checks.has_permissions(administrator=True)
    @subject.subcommand(name="add")
    async def subject_add(
        self,
        interaction: Interaction,
        subject_name: str = SlashOption(name="name", description="the subject's name"),
        subject_emoji: str = SlashOption(
            name="emoji", description="the subject's emoji"
        ),
    ):
        confirm_embed = Embed(
            title="Are you sure of these informations?",
            description=f"``Subject name:`` {subject_name}\n``emoji:``{subject_emoji}",
            colour=EMBED_COLOR,
        )
        fail_embed = Embed(color=EMBED_COLOR)
        success_embed = Embed(
            title="Subject added",
            description=f"Subject '{subject_emoji}{subject_name}' has been added !",
            color=EMBED_COLOR,
        )

        existing_names = await self.db.get_fetchall("SELECT Name FROM 'Subjects' WHERE GuildId=?", (interaction.guild_id,))
        existing_names = [name[0].lower() for name in existing_names]

        if subject_name.lower() in existing_names:
            fail_embed.title = "Subject already exists"
            fail_embed.description = f"The subject '{subject_name}' already exists, please try again using another name"
            await interaction.response.send_message(embed=fail_embed, ephemeral=True)
            return
        
        confirm_view = Confirm()
        await interaction.response.send_message(
            embed=confirm_embed, view=confirm_view, ephemeral=True
        )

        await confirm_view.wait()

        if not confirm_view.value:
            fail_embed.title="Operation cancelled"
            await interaction.edit_original_message(embed=fail_embed, view=None)
            return

        await self.db.request(
            """INSERT INTO 'Subjects'('GuildId', 'Name', 'Emoji') VALUES(?,?,?)""",
            (
                interaction.guild_id,
                subject_name.lower(),
                subject_emoji,
            ),
        )
        lessons_category = interaction.guild.get_channel(await get_constant_id(interaction.guild_id, "LessonsCategoryId"))
        await lessons_category.create_text_channel(name=f"{subject_emoji} {subject_name.lower()}")
        await interaction.edit_original_message(embed=success_embed, view=None)


    @application_checks.has_permissions(administrator=True)
    @subject.subcommand(name="remove")
    async def subject_remove(
        self,
        interaction: Interaction,
        subject_name: str = SlashOption(name="name", description="the subject's name"),
    ):
        confirm_embed = Embed(
            title="Are you sure you want to remove this subject?",
            description=f"``Subject name:`` {subject_name}",
            colour=EMBED_COLOR,
        )
        fail_embed = Embed(color=EMBED_COLOR)
        success_embed = Embed(
            title="Subject Removed",
            description=f"Subject '{subject_name}' has been removed !",
            color=EMBED_COLOR,
        )

        existing_names = await self.db.get_fetchall("SELECT Name FROM 'Subjects' WHERE GuildId=?", (interaction.guild_id,))
        existing_names = [name[0].lower() for name in existing_names]

        if not subject_name.lower() in existing_names:
            fail_embed.title = "Subject does not exist"
            fail_embed.description = f"The subject '{subject_name}' Does not exist, please verify the subject name and try again"
            await interaction.response.send_message(embed=fail_embed, ephemeral=True)
            return
        
        confirm_view = Confirm()
        await interaction.response.send_message(
            embed=confirm_embed, view=confirm_view, ephemeral=True
        )

        await confirm_view.wait()

        if not confirm_view.value:
            fail_embed.title="Operation cancelled"
            await interaction.edit_original_message(embed=fail_embed, view=None)
            return

        await self.db.request(
            "DELETE FROM Subjects WHERE GuildId=? AND Name=?",
            (
                interaction.guild_id,
                subject_name.lower(),
            ),
        )

        lessons_category = interaction.guild.get_channel(await get_constant_id(interaction.guild_id, "LessonsCategoryId"))
        try:
            for subject_channel in lessons_category.channels:
                if subject_name.lower() in subject_channel.name:
                    await subject_channel.delete()
                    break
        except:
            pass
        await interaction.edit_original_message(embed=success_embed, view=None)


    @application_checks.has_permissions(administrator=True)
    @subject.subcommand(name="list")
    async def subject_list(self, interaction : Interaction):
        subjects = await self.db.get_fetchall("SELECT Name, Emoji FROM Subjects WHERE GuildId=?", (interaction.guild_id,))
        print(subjects)
        subjects = [f"- {subject_emoji} {subject_name}" for subject_name, subject_emoji in subjects]

        list_embed = Embed(
            title=f"List of Subjects in {interaction.guild.name}",
            description="\n".join(subjects) if subjects else "No subjects yet",
            color=Color.blue()
        )
        list_embed.set_thumbnail(url=interaction.guild.icon)
        await interaction.response.send_message(embed=list_embed)


def setup(client: Bot):
    client.add_cog(Moderation(client))
