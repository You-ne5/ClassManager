import asyncio
from nextcord.ext.commands import Bot, Cog
from nextcord.ext import application_checks
from nextcord import slash_command, Embed, Color, Interaction, TextChannel

from utils.views import HelpView, HelpPanel


class Moderation(Cog):
    def __init__(self, client: Bot) -> None:
        self.client = client

    @Cog.listener()
    async def on_ready(self):
        self.client.add_view(HelpView(self.client))
        self.client.add_view(HelpPanel())
        return
    
    
    @application_checks.has_permissions(administrator=True)
    @slash_command(name="clear")
    async def clear(self, interaction:Interaction, channel: TextChannel = None, amount : int = None):
        to_clear = channel if channel else interaction.channel

        loading_clear=Embed(
            title=f"Clearing {to_clear.name}",
            colour=Color.yellow(),
            )
        loading_clear.set_author(name=self.client.user.name, url=self.client.user.avatar)

        cleared=Embed(
            title="Cleared!", 
            description=f" {to_clear.name} has been cleared!",
            colour=Color.green()
        )
        cleared.set_author(name=self.client.user.name, url=self.client.user.avatar)

        messages = []
        
        for chnl in ([channel, interaction.channel] if channel else [interaction.channel]):
            msg = await chnl.send(embed=loading_clear)
            if channel and chnl != channel: messages.append(msg)

        await to_clear.purge(limit=amount)


        for message in messages:
            await message.delete()

        messages = []

        for chnl in ([channel, interaction.channel] if channel else [interaction.channel]):
            messages.append(await chnl.send(embed=cleared))

        await asyncio.sleep(3)


        for message in messages:
            await message.delete()


    @application_checks.has_permissions(administrator=True)
    @slash_command(name="setup_help")
    async def setup_help(self, interaction : Interaction):
        help_embed = Embed(
            title="Get help",
            description="Choose the subject you need help with:",
            color=Color.blurple()
        )
        await interaction.response.send_message(embed=help_embed, view=HelpView(self.client))



def setup(client: Bot):
    client.add_cog(Moderation(client))
