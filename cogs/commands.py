from nextcord.ext.commands import Bot, Cog
from nextcord.ext import application_checks
from nextcord import slash_command, Embed, Color, Interaction, SlashOption, TextChannel, Attachment

from config import ANNOUNCE_CHANNEL_ID, EMBED_COLOR
from utils.views import Confirm
from utils.functions import pgcd, ppcm, eq_2
from aiosqlite import Connection, Cursor


class Annonce(Cog):
    def __init__(self, client: Bot) -> None:
        self.client = client

    async def connect_db(self):
        self.db: Connection = self.client.db
        self.cursor: Cursor = await self.db.cursor()

    @Cog.listener()
    async def on_ready(self):
        return
    

    @slash_command(name="announce")
    async def announce(
        self, 
        interaction: Interaction,
        title : str = SlashOption(required=True, name="title"),
        description : str = SlashOption(required=True, name="description"),
        image : Attachment = SlashOption(required=False, name= "image")
        ):

        valid_image = any(word in image.content_type for word in ["image", "png", "jpeg"]) if image else False

        announce_embed = Embed(
            title=title, 
            description=description, 
            colour=0xba7b0d
            )
        announce_embed.set_author(
            icon_url=interaction.user.avatar, 
            name=f"from {interaction.user.nick.split()[0]}"
            )
        announce_channel = interaction.guild.get_channel(ANNOUNCE_CHANNEL_ID)
        
        confirm_embed = Embed(
            title="Are you sure of making this announcement?", 
            description=f"``title:`` {title}\n``description:`` {description}\n{'``image:``' if valid_image else ''}", 
            colour=Color.blue()
            )
        
        success_embed = Embed(
            title="Announce made successfully !", 
            description=f"Check {announce_channel.mention}", 
            colour=Color.green()
            )
        
        fail_embed = Embed(
            title="Announcement canceled !",
            colour=Color.red()
            )
        
        if valid_image:
            announce_embed.set_image(image)
            confirm_embed.set_image(image)

        confirm_view = Confirm()
        
        await interaction.response.send_message(embed=confirm_embed, view=confirm_view, ephemeral=True)
        await confirm_view.wait()
        
        if confirm_view.value:
            await announce_channel.send(embed=announce_embed, content="@everyone")
            await interaction.edit_original_message(embed=success_embed, view=None)
        else:
            await interaction.edit_original_message(embed=fail_embed, view=None)
    
    @slash_command(name="pgcd")
    async def pgcd(
        self, 
        interaction : Interaction, 
        a : int = SlashOption(required=True, name="a"), 
        b : int = SlashOption(required=True, name="b")
        ):
        d = pgcd(a, b)
        embed = Embed(
            title=f"PGCD({a}, {b}) = {d}",
            color=EMBED_COLOR
        )
        await interaction.response.send_message(embed=embed)

    @slash_command(name="ppcm")
    async def ppcm(
        self, 
        interaction : Interaction, 
        a : int = SlashOption(required=True, name="a"), 
        b : int = SlashOption(required=True, name="b")
        ):
        m = ppcm(a, b)
        embed = Embed(
            title=f"PPCM({a}, {b}) = {m}",
            color=EMBED_COLOR
        )
        await interaction.response.send_message(embed=embed)


    @slash_command(name="equation_2_var", description="ax + by = c")
    async def equation_2_var(
        self, 
        interaction : Interaction, 
        a : int = SlashOption(required=True, name="a"), 
        b : int = SlashOption(required=True, name="b"),
        c : int = SlashOption(required=True, name="c"),
        ):

        d = pgcd(a, b)
        a//=d
        b//=d
        c//=d
        if any(i > 10000 for i in (a, b, c)):
            await interaction.response.send_message("matethamesch manich pc ta3 nasa")
            return

        solutions = eq_2(a, b, c)
        if solutions:
            solutions = ', '.join(solutions)

        embed = Embed(
            title=f"حلول معادلة ذات مجهولين",
            description=f"``equasion:`` {a}x + {b}y = {c}\n``Solutions:`` {f'(x, y) = ({solutions})' if solutions else 'لا تقبل حلول'}",
            color=EMBED_COLOR
        )
        await interaction.response.send_message(embed=embed)


def setup(client: Bot):
    client.add_cog(Annonce(client))
