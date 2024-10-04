from nextcord.ext.commands import Bot, Cog
from nextcord import (
    Embed,
    Interaction,
    Message,
    CategoryChannel,
    Member,
    PermissionOverwrite
)

from config import EMBED_COLOR
from utils.views import HelpView, HelpPanel, ValidateView, ValidationModal
from utils.functions import message_verif
from utils.get_functions import get_constant_id
from utils.db import DB

class Events(Cog):
    def __init__(self, client: Bot) -> None:
        self.client = client


    async def connect_db(self):
        self.db = DB()
        await self.db.load_db("main.db")


    @Cog.listener()
    async def on_ready(self):
        await self.connect_db()
        return


    @Cog.listener()
    async def on_interaction(self, interaction : Interaction):
        if not interaction.data.get("custom_id") == "help_subject":
            return
        
        help_category : CategoryChannel = interaction.guild.get_channel(await get_constant_id(interaction.guild_id, "HelpCategoryId"))
        user_name = interaction.user.nick.split()[0] if interaction.user.nick else interaction.user.name
        help_channel = await help_category.create_text_channel(f"{user_name}-{interaction.data["values"][0]}")

        self.db = DB()
        await self.db.load_db("main.db")

        await self.db.request("INSERT INTO HelpChannels Values (?,?,?)", (interaction.guild.id, help_channel.id, interaction.user.id))

        help_channel_embed = Embed(
            title=f"{user_name}'s Help channel",
            description="explain your problem in one message (providing pictures), a classmate will come to help you",
            color=EMBED_COLOR
        )
        try:
            await interaction.response.send_message(f"help channel created: {help_channel.mention}", ephemeral=True, delete_after=5)
        except:
            pass

        await help_channel.send(embed=help_channel_embed, content=f"{interaction.user.mention}", view=HelpPanel(client=self.client))
        
        subjects = await self.db.get_fetchall("SELECT Name, Emoji FROM Subjects WHERE GuildId=?", (interaction.guild_id,))
        await interaction.message.edit(view=HelpView(client=self.client, subjects=subjects))

        def is_allowed(message: Message):
            return message.author.id == interaction.user.id and message.channel.id == help_channel.id

        try:
            await self.client.wait_for("message", timeout=600, check=is_allowed)
        except TimeoutError:                
            await help_channel.delete()
            return
        else:
            await help_channel.send(f"@everyone", delete_after=2)


    @Cog.listener()
    async def on_message(self, message: Message):

        if not message.guild:
            return
        
        lessons_category_id = await get_constant_id(message.guild.id, "LessonsCategoryId")
        channel = message.channel
        alert_embed = Embed(
            title="Invalid message", 
            description=f"Only messages containing links/images/files are allowed in the channel: {channel.name}",
            color=EMBED_COLOR
            )

        if message.author.id == self.client.user.id:
            return
        if (
            message.channel.category.id == lessons_category_id
            and not message_verif(message)
        ):
            await message.delete()
            await message.author.send(embed=alert_embed)


def setup(client: Bot):
    client.add_cog(Events(client))
