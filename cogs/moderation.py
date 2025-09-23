import asyncio
from nextcord.ext.commands import Bot, Cog
from nextcord.ext import application_checks
from nextcord import (
    slash_command,
    Embed,
    Color,
    Interaction,
    TextChannel,
    Member,
    SlashOption,
    Attachment
)

from config import EMBED_COLOR
from utils.views import HelpView, HelpPanel, ValidateView, Confirm
from utils.functions import create_constant
from utils.get_functions import get_constant_id
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
        self.client.add_view(ValidateView())

        return

    @application_checks.has_permissions(administrator=True)
    @slash_command(name="setup_validation")
    async def setup_validation(self, interaction : Interaction):
        validation_embed = Embed(
            title="Account Validation",
            description=f"Welcome to `{interaction.guild.name}`, to acces the discord server validate your account using the button below.\n\nif you have trouble validating your account, send a message here, or tag a moderator",
            color=EMBED_COLOR
        )

        await interaction.response.send_message("done", ephemeral=True)
        await interaction.channel.send(embed=validation_embed, view=ValidateView())

    @application_checks.has_permissions(administrator=True)
    @slash_command(name="send")
    async def send(
        self, 
        interaction: Interaction,
        title : str = SlashOption(required=True, name="title"),
        description : str = SlashOption(required=False, name="description"),
        content : str = SlashOption(required=False, name="content"),
        image : Attachment = SlashOption(required=False, name= "image"),
        channel1 : TextChannel = SlashOption(required=False, name="channel1"),
        channel2 : TextChannel = SlashOption(required=False, name="channel2"),
        channel3 : TextChannel = SlashOption(required=False, name="channel3"),
        channel4 : TextChannel = SlashOption(required=False, name="channel4"),
        channel5 : TextChannel = SlashOption(required=False, name="channel5"),
        channel6 : TextChannel = SlashOption(required=False, name="channel6"),
        ):

        valid_image = any(word in image.content_type for word in ["image", "png", "jpeg"]) if image else False

        announce_embed = Embed(
            title=title, 
            description=description, 
            colour=0xba7b0d
            )
        
        author_name = interaction.user.nick if interaction.user.nick else interaction.user.name
        announce_embed.set_author(
            icon_url=interaction.user.avatar, 
            name=f"from {author_name}"
            )
        channels_to_send = [channel for channel in [channel1, channel2, channel3, channel4, channel5, channel6] if channel]
        if not channels_to_send:
            channels_to_send = [interaction.channel]
        channel_names = [channel.name for channel in channels_to_send]

        confirm_embed = Embed(
            title="Are you sure of sending this message?", 
            description=f"``title:`` {title}\n``description:`` {description}\n``channels:`` {', '.join(channel_names)}\n{'``image:``' if valid_image else ''}", 
            colour=Color.blue()
            )
        
        success_embed = Embed(
            title="Message sent successfully !", 
            description=f"Check {' '.join(channel.mention for channel in channels_to_send)}", 
            colour=Color.green()
            )
        
        fail_embed = Embed(
            title="Sending canceled !",
            colour=Color.red()
            )
        
        if valid_image:
            announce_embed.set_image(image)
            confirm_embed.set_image(image)

        confirm_view = Confirm()
        
        await interaction.response.send_message(embed=confirm_embed, view=confirm_view, ephemeral=True)
        await confirm_view.wait()
        
        if confirm_view.value:
            for channel in channels_to_send:
                await channel.send(embed=announce_embed, content=content)
                await interaction.edit_original_message(embed=success_embed, view=None)
        else:
            await interaction.edit_original_message(embed=fail_embed, view=None)


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
        fail_embed = Embed(
                title="HAC not configured",
                description="help archive category hasn't been configured yet or category no longer exists, use '/config hac' to configure it",
                color=Color.red()
            )
        
        hac_id = await get_constant_id(interaction.guild.id, "HelpArchiveCategoryId")
        hac_category = interaction.guild.get_channel(hac_id if hac_id else 0)
        subjects = await self.db.get_fetchall("SELECT Name, Emoji FROM Subjects WHERE GuildId=?", (interaction.guild_id,))

        if hac_category:
            if not subjects:
                help_embed.title = "No subjects added !"
                help_embed.description = "There are no subjects configured, use /subject_add to configure new subjects"
            if subjects:
                await interaction.response.send_message(
                    embed=help_embed, view=HelpView(client=self.client, subjects=subjects)
                )
            else:
                await interaction.response.send_message(embed=help_embed)
        else:
            await interaction.response.send_message(embed=fail_embed)


    @application_checks.has_permissions(administrator=True)
    @slash_command(name="setup", description="Setup the bot")
    async def setup(self, interaction : Interaction):

        guild_id = interaction.guild_id
        constants_created = []
        return_embed = Embed(title="Bot has been Setup seccessfully", color=EMBED_COLOR)
        loading_embed = Embed(title="Setup in process...", color=EMBED_COLOR)
        loading_message = await interaction.response.send_message(embed=loading_embed)

        guild_constants = await self.db.get_fetchone("SELECT * FROM GuildsConstants WHERE GuildId=?", (guild_id,))

        if guild_constants:
            help_category = interaction.guild.get_channel(guild_constants[1])
            help_archive_category = interaction.guild.get_channel(guild_constants[2])
            lessons_category = interaction.guild.get_channel(guild_constants[3])
            exo_channel = interaction.guild.get_channel(guild_constants[4])
            announce_channel = interaction.guild.get_channel(guild_constants[5])
            validation_category = interaction.guild.get_channel(guild_constants[6] if guild_constants[6] else None)
            student_role = interaction.guild.get_role(guild_constants[7] if guild_constants[7] else None)

            if not help_category:
                await create_constant(interaction, "HelpCategoryId")
                constants_created.append("help category")
            if not help_archive_category:
                await create_constant(interaction, "HelpArchiveCategoryId")
                constants_created.append("help archive")
            if not lessons_category:
                await create_constant(interaction, "LessonsCategoryId")
                constants_created.append("Lessons")
            if not exo_channel:
                await create_constant(interaction, "ExoChannelId")
                constants_created.append("exercice channel")
            if not announce_channel:
                await create_constant(interaction, "AnnounceChannelId")
                constants_created.append("announce channel")
            if not student_role:
                await create_constant(interaction, "StudentRoleId")
                constants_created.append("Students role")
            if not validation_category:
                await create_constant(interaction, "ValidationCategoryId")
                constants_created.append("Validation category")
        else:
            await self.db.request("INSERT INTO 'GuildsConstants' VALUES (?,?,?,?,?,?,?,?)", (guild_id, None, None, None, None, None, None, None))

            constants_created = ["HelpCategoryId", "HelpArchiveCategoryID", "LessonsCategoryId", "ExoChannelId", "AnnounceChannelId", "ValidationCategoryId", "StudentRoleId"]

            for constant_name in constants_created:
                await create_constant(interaction, constant_name)
        
        if constants_created:
            return_embed.description = "**Added Constants:**\n"
            return_embed.description += "\n".join([f"- {s}" for s in constants_created])

        await loading_message.edit(embed=return_embed)


def setup(client: Bot):
    client.add_cog(Moderation(client))
