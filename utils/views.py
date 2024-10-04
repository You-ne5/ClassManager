from config import EMBED_COLOR, OWNER_ID
from utils.db import DB
from utils.functions import get_constant_id

from nextcord import *
from nextcord.interactions import Interaction
from nextcord.ext.commands import Bot


class Confirm(ui.View):
    def __init__(self):
        super().__init__()
        self.value = None

    @ui.button(label="Confirm", style=ButtonStyle.green)
    async def confirm(self, button: ui.Button, interaction: Interaction):
        self.value = True
        self.stop()

    @ui.button(label="Cancel", style=ButtonStyle.grey)
    async def cancel(self, button: ui.Button, interaction: Interaction):
        self.value = False
        self.stop()


class Confirm(ui.View):
    def __init__(self):
        super().__init__()
        self.value = None

    @ui.button(label="Validate", style=ButtonStyle.green)
    async def validate(self, button: ui.Button, interaction: Interaction):
        db = DB()
        await db.load_db("main.db")

        sections = await db.get_fetchall("SELECT Identifier FROM Sections WHERE GuildId=?", (interaction.guild_id,))
        sections = [identifier[0] for identifier in sections]

        groups = await db.get_fetchall("SELECT Number FROM Groups WHERE GuildId=?", (interaction.guild_id,))
        groups = [number[0] for number in groups]

        await interaction.response.send_modal(ValidationModal(sections, groups))


class HelpView(ui.View):
    def __init__(self, client: Bot, subjects: list[tuple[str]]):
        super().__init__(timeout=None)

        self.client = client

        self.add_item(HelpSelect(client=self.client, subjects=subjects))


class HelpSelect(ui.Select):
    def __init__(self, client: Bot, subjects: list[tuple[str]]):
        self.client = client

        options = [
            SelectOption(label=subject[0], emoji=subject[1]) for subject in subjects
        ]

        super().__init__(
            placeholder="Choose the subject you need help with",
            custom_id="help_subject",
            max_values=1,
            min_values=1,
            options=options,
        )


class HelpPanel(ui.View):
    def __init__(self, client: Bot):
        super().__init__(timeout=None)
        self.client = client
        return

    async def can_close(self, interaction: Interaction):

        self.db = DB()
        await self.db.load_db("main.db")

        author_id = await self.db.get_fetchone(
            "SELECT AuthorId FROM HelpChannels WHERE ChannelId=?",
            (interaction.channel.id,),
        )
        if interaction.user.id == OWNER_ID:
            can_close = True
        else:
            can_close = bool(interaction.user.id == author_id[0])

        return can_close

    @ui.button(
        label="Close channel",
        style=ButtonStyle.red,
        custom_id="close_helpchannel_button",
    )
    async def close_help(self, button: ui.Button, interaction: Interaction):
        can_close = await self.can_close(interaction=interaction)

        if can_close:

            confirm_embed = Embed(
                title="Confirmation",
                description="Are you sure you want to close this channel?",
                colour=Color.blue(),
            )
            confirm_view = Confirm()

            await interaction.response.send_message(
                embed=confirm_embed, view=confirm_view, ephemeral=True
            )
            await confirm_view.wait()

            if confirm_view.value:

                perms = {
                    interaction.guild.default_role: PermissionOverwrite(
                        view_channel=True, send_messages=False
                    )
                }
                HELP_ARCHIVE_CATEGORY_ID = await get_constant_id(
                    interaction.guild.id, "HelpArchiveCategoryId"
                )
                help_archive_category: CategoryChannel = interaction.guild.get_channel(
                    HELP_ARCHIVE_CATEGORY_ID
                )
                archive_channel_name = f"{interaction.channel.name}-1"

                for channel in help_archive_category.channels:
                    if channel.name == archive_channel_name:
                        archive_channel_name = f"{archive_channel_name[:-1]}{str(int(channel.name[-1]) + 1)}"

                try:
                    await interaction.channel.edit(
                        name=archive_channel_name,
                        category=help_archive_category,
                        overwrites=perms,
                    )
                except errors.HTTPException:
                    sorted_channels = sorted(
                        help_archive_category.channels, key=lambda c: c.created_at
                    )
                    await sorted_channels[0].delete()
                    await interaction.channel.edit(
                        name=archive_channel_name,
                        category=help_archive_category,
                        overwrites=perms,
                    )

                await interaction.channel.send(
                    embed=Embed(title="Channel closed", color=EMBED_COLOR)
                )
                await interaction.message.edit(view=None)

            else:
                await interaction.edit_original_message(
                    content="closing canceled", embed=None, view=None
                )
        else:
            await interaction.response.send_message(
                "permission denied", ephemeral=True, delete_after=3
            )


class ValidationModal(ui.Modal):
    def __init__(self, guild_sections: list, guild_groups : list):
        super().__init__(
            title="Validation Form",
            custom_id="validation-modal",
        )

        self.first_name = ui.TextInput(
            label="First Name",
            min_length=2,
            max_length=20,
            required=True,
            placeholder="Enter your first name",
        )
        self.last_name = ui.TextInput(
            label="Last Name",
            min_length=2,
            max_length=20,
            required=True,
            placeholder="Enter your last name",
        )
        self.section = ui.TextInput(
            label="Section",
            min_length=1,
            required=True,
            placeholder=f"Enter your section identifier ({', '.join(guild_sections)})",
        )
        self.group = ui.TextInput(
            label="Group",
            min_length=1,
            required=True,
            placeholder=f"Enter your Group number ({', '.join(guild_groups)})",
        )
