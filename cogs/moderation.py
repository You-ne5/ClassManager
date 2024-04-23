import asyncio
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
    CategoryChannel
)
from aiosqlite import Connection, Cursor

from config import EMBED_COLOR, HELP_ARCHIVE_CATEGORY_ID
from utils.views import HelpView, HelpPanel, Confirm
from config import LESSONS_CATEGORY_ID


class Moderation(Cog):
    def __init__(self, client: Bot) -> None:
        self.client = client

    async def connect_db(self):
        self.db: Connection = self.client.db
        self.cursor: Cursor = await self.db.cursor()

    @Cog.listener()
    async def on_ready(self):
        await self.connect_db()
        self.client.add_view(HelpView(client=self.client))
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
            description=f"Subject {subject_name,subject_emoji} has been added !",
            color=EMBED_COLOR,
        )

        res = await self.cursor.execute("SELECT name FROM subjects")
        existing_names = await res.fetchall()
        existing_names = [name[0] for name in existing_names]

        if subject_name in existing_names:
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

        await self.cursor.execute(
            """INSERT INTO 'subjects'('name', 'emoji') VALUES(?,?)""",
            (
                subject_name,
                subject_emoji,
            ),
        )
        await self.db.commit()

        await interaction.edit_original_message(embed=success_embed, view=None)

    # @application_checks.has_permissions(administrator=True)
    # @slash_command(name="test")
    # async def test(self, interaction: Interaction):
    #     for i in range(47):
    #         help_archive_category : CategoryChannel = interaction.guild.get_channel(HELP_ARCHIVE_CATEGORY_ID)
    #         await interaction.guild.create_text_channel(name=f"{i}", category=help_archive_category)

    @application_checks.has_permissions(administrator=True)
    @slash_command(name="clear")
    async def clear(
        self, interaction: Interaction, channel: TextChannel = None, amount: int = None
    ):
        to_clear = channel if channel else interaction.channel

        loading_clear = Embed(
            title=f"Clearing {to_clear.name}",
            colour=Color.yellow(),
        )
        loading_clear.set_author(
            name=self.client.user.name, url=self.client.user.avatar
        )

        cleared = Embed(
            title="Cleared!",
            description=f" {to_clear.name} has been cleared!",
            colour=Color.green(),
        )
        cleared.set_author(name=self.client.user.name, url=self.client.user.avatar)

        messages = []

        for chnl in (
            [channel, interaction.channel] if channel else [interaction.channel]
        ):
            msg = await chnl.send(embed=loading_clear)
            if channel and chnl != channel:
                messages.append(msg)

        await to_clear.purge(limit=amount)

        for message in messages:
            await message.delete()

        messages = []

        for chnl in (
            [channel, interaction.channel] if channel else [interaction.channel]
        ):
            messages.append(await chnl.send(embed=cleared))

        await asyncio.sleep(3)

        for message in messages:
            await message.delete()

    @application_checks.has_permissions(administrator=True)
    @slash_command(name="setup_help")
    async def setup_help(self, interaction: Interaction):
        help_embed = Embed(
            title="Get help",
            description="Choose the subject you need help with:",
            color=EMBED_COLOR,
        )
        await interaction.response.send_message(
            embed=help_embed, view=HelpView(client=self.client)
        )

    @Cog.listener()
    async def on_message(self, message: Message):
        if message.author.id == self.client.user.id:
            return

        if (
            message.channel.category.id == LESSONS_CATEGORY_ID
            and not message.attachments
        ):
            await message.delete()
            await message.channel.send(
                content=f"{message.author.mention} text messages aren't allowed in this channel",
                delete_after=6,
            )


def setup(client: Bot):
    client.add_cog(Moderation(client))
