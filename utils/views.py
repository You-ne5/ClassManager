from nextcord import *
from nextcord.interactions import Interaction
from config import HELP_CATEGORY_ID, HELP_ARCHIVE_CATEGORY_ID, EMBED_COLOR
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


class HelpView(ui.View):
    def __init__(
        self,
        client : Bot,
    ):
        super().__init__(timeout=None)

        self.client = client

        self.add_item(
            HelpSelect(client=self.client)
            )
        


class HelpSelect(ui.Select):
    def __init__(
        self, 
        client : Bot
    ):
        self.client = client

        math_select = SelectOption(label="Math", description="", emoji="📐")
        physics_select = SelectOption(label="Physique", description="", emoji="🛰")
        science_select = SelectOption(label="Science", description="", emoji="🧪")
        français_select = SelectOption(label="Français", description="", emoji="🗼")
        english_select = SelectOption(label="English", description="", emoji="🎩")
        arabic_select = SelectOption(label="عربية", description="", emoji="📖")
        charia_select = SelectOption(label="شريعة", description="", emoji="🕋")
        history_select = SelectOption(label="Histoire", description="", emoji="📜")
        geo_select = SelectOption(label="Geo", description="", emoji="🌍")
        philo_select = SelectOption(label="Philosophy", description="", emoji="🧠")

            
        options = [
            math_select, 
            physics_select, 
            science_select, 
            français_select, 
            english_select, 
            arabic_select, 
            charia_select, 
            history_select, 
            geo_select, 
            philo_select
            ]

        super().__init__(
            placeholder="Choose the subject you need help with",
            custom_id="help_subject",
            max_values=1,
            min_values=1,
            options=options,
        )

    async def callback(self, interaction: Interaction) -> None:
        help_category : CategoryChannel = interaction.guild.get_channel(HELP_CATEGORY_ID)
        help_channel = await help_category.create_text_channel(f"{interaction.user.nick.split()[0]}-{self.values[0]}")
        
        help_channel_embed = Embed(
            title=f"{interaction.user.nick.split()[0]}'s Help channel",
            description="explain your problem in one message (providing pictures), a classmate will come to help you",
            color=EMBED_COLOR
        )
        await interaction.response.send_message(f"help channel created: {help_channel.mention}", ephemeral=True, delete_after=5)
        await help_channel.send(embed=help_channel_embed, content=f"{interaction.user.mention}", view=HelpPanel())
        
        await interaction.message.edit(view=HelpView(client=self.client))


        def is_allowed(message: Message):
            return message.author.id == interaction.user.id and message.channel.id == help_channel.id

        try:
            await self.client.wait_for("message", timeout=600, check=is_allowed)
        except TimeoutError:                
            await help_channel.delete()
            return
        else:
            await help_channel.send(f"@everyone", delete_after=2)



class HelpPanel(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        return
    
    @ui.button(label="Close channel", style=ButtonStyle.red, custom_id="close_helpchannel_button")
    async def close_help(self, button: ui.Button, interaction: Interaction):

        if interaction.channel.name.startswith(interaction.user.nick.split()[0].lower()): 

            confirm_embed = Embed(
            title="Confirmation",
            description="Are you sure you want to close this channel?",
            colour=Color.blue()
            )
            confirm_view = Confirm()
        
            await interaction.response.send_message(embed=confirm_embed, view=confirm_view, ephemeral=True)
            await confirm_view.wait()

            if confirm_view.value:
                perms = {interaction.guild.default_role : PermissionOverwrite(view_channel=True, send_messages=False)}
                help_archive_category : CategoryChannel = interaction.guild.get_channel(HELP_ARCHIVE_CATEGORY_ID)
                archive_channel_name = f"{interaction.channel.name}-1"

                n=0

                for channel in help_archive_category.channels:
                    if channel.name==archive_channel_name:
                        archive_channel_name = f"{archive_channel_name[:-1]}{str(int(channel.name[-1]) + 1)}"


                await interaction.channel.edit(name=archive_channel_name, category=help_archive_category, overwrites=perms)
                await interaction.channel.send(embed=Embed(title="Channel closed", color=EMBED_COLOR))
            else:
                await interaction.edit_original_message(content="closing canceled", embed=None, view=None)
        else:
            return