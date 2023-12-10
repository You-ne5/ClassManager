from nextcord.ext.commands import Bot, Cog
from nextcord.ext import application_checks
from nextcord import slash_command, Embed, Color, Interaction, SlashOption, TextChannel, Attachment

from config import DLG_ID, ADMIN_ROLE_ID, ANNOUNCE_CHANNEL_ID
from utils.views import Confirm


class Annonce(Cog):
    def __init__(self, client: Bot) -> None:
        self.client = client

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
        # print(image.content_type)

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



def setup(client: Bot):
    client.add_cog(Annonce(client))
