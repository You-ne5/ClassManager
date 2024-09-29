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

from config import EMBED_COLOR
from utils.views import HelpView, HelpPanel, Confirm
from utils.functions import get_hac_id, message_verif
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

        await self.db.request(
            """INSERT INTO 'subjects'('name', 'emoji') VALUES(?,?)""",
            (
                subject_name,
                subject_emoji,
            ),
        )

        await interaction.edit_original_message(embed=success_embed, view=None)


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
        
        hac_id = await get_hac_id(guild_id=interaction.guild.id, cursor=self.cursor)
        hac_category = interaction.guild.get_channel(hac_id if hac_id else 0)
        if hac_category:
            await interaction.response.send_message(
                embed=help_embed, view=HelpView(client=self.client)
            )
        else:
            await interaction.response.send_message(embed=fail_embed)


    @Cog.listener()
    async def on_message(self, message: Message):
        lessons_category_id = 0 #to change
        if message.author.id == self.client.user.id:
            return
        if (
            message.channel.category.id == lessons_category_id
            and not message_verif(message)
        ):
            await message.delete()
            await message.channel.send(
                content=f"{message.author.mention} text messages aren't allowed in this channel",
                delete_after=6,
            )
    

    @slash_command(name="config")
    async def config(self, interaction : Interaction):
        return


    @config.subcommand(name="hac", description="configure Help Archive Category")
    async def config_HAC(self, interaction : Interaction, category : CategoryChannel = SlashOption(name="category")):
        response_embed = Embed(
                title=None,
                description=None,
                color=EMBED_COLOR
            )
        try:
            HAC_id = await self.db.get_fetchone("SELECT HelpArchiveCategoryID FROM Channels WHERE GuildID=?", (interaction.guild.id,))

            if HAC_id:
                await self.db.request("UPDATE Channels SET HelpArchiveCategoryID=? WHERE GuildID=?", (category.id, interaction.guild.id))
            else:
                await self.db.request("INSERT INTO Channels VALUES (?,?,?)", (category.id, interaction.guild.id, 0))

            response_embed.title = "HAC configued successfully!"
            response_embed.description = f"Help Archive Category is now {category.mention}"

        except Exception as error:
            response_embed.title = "something went wrong"
            response_embed.description = str(error)
            response_embed.color = Color.red()

        await interaction.response.send_message(embed=response_embed)          


    @slash_command(name="add")
    def add(self, interaction : Interaction):
        return
    

    @add.subcommand(name="subject")
    def add_subject(self, interaction : Interaction, name : str, emoji : str):
        pass


def setup(client: Bot):
    client.add_cog(Moderation(client))
