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
from utils.views import Confirm
from utils.db import DB

class Sections(Cog):
    def __init__(self, client: Bot) -> None:
        self.client = client


    async def connect_db(self):
        self.db = DB()
        await self.db.load_db("main.db")


    @Cog.listener()
    async def on_ready(self):
        await self.connect_db()
        return

    @slash_command(name="section")
    async def section(self, interaction : Interaction):
        return
    
    @section.subcommand(name="add", description="Creates a section, with a role and a specific category")
    async def section_add(
        self, 
        interaction : Interaction, 
        identifier : str
        ):
        confirm_embed = Embed(
            title="Are you sure of these informations?",
            description=f"``Section Identifier:`` {identifier}",
            colour=EMBED_COLOR,
        )
        fail_embed = Embed(color=EMBED_COLOR)
        success_embed = Embed(
            title="Section created !",
            description=f"The section '{identifier}' has been created !",
            color=EMBED_COLOR,
        )

        existing_identifiers = await self.db.get_fetchall("SELECT Identifier FROM 'Sections' WHERE GuildId=?", (interaction.guild_id,))
        existing_identifiers = [name[0].lower() for name in existing_identifiers]

        if identifier.lower() in existing_identifiers:
            fail_embed.title = "Section already exists"
            fail_embed.description = f"The Section '{identifier}' already exists, please try again using another identifier"
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
        
        section_role = await interaction.guild.create_role(name=f"Section {identifier.upper()}")

        category_perms = {
            interaction.guild.default_role : PermissionOverwrite(view_channel=False, send_messages=False),
            section_role : PermissionOverwrite(view_channel=True, send_messages=True)
        }
        section_category = await interaction.guild.create_category(
            name=f"Section {identifier.upper()}",
            overwrites=category_perms
            )
        
        await section_category.create_text_channel(name=f"✍conversation-s-{identifier}")
        await section_category.create_text_channel(name=f"❓questions")
        await section_category.create_voice_channel(name=f"Study class {identifier}")

        await self.db.request(
            """INSERT INTO 'Sections'('GuildId', 'Identifier', 'RoleId', 'CategoryId') VALUES(?,?,?,?)""",
            (
                interaction.guild_id,
                identifier.lower(),
                section_role.id,
                section_category.id
            ),
        )

        await interaction.edit_original_message(embed=success_embed, view=None)


    @section.subcommand(name="remove", description="Removes a section")
    async def section_remove(
        self, 
        interaction : Interaction, 
        identifier : str
        ):
        confirm_embed = Embed(
            title="Are you sure You want to delete this section?",
            description=f"``Section :`` {identifier}",
            colour=EMBED_COLOR,
        )
        fail_embed = Embed(color=EMBED_COLOR)
        success_embed = Embed(
            title="Section Deleted !",
            description=f"The section '{identifier}' has been deleted !",
            color=EMBED_COLOR,
        )

        section_info = await self.db.get_fetchall("SELECT Identifier FROM 'Sections' WHERE GuildId=?", (interaction.guild_id,))
        existing_identifiers = [name[0].lower() for name in section_info]

        if not identifier.lower() in existing_identifiers:
            fail_embed.title = "Section doesn't exist!"
            fail_embed.description = f"The Section '{identifier}' does not exist, please try again using another identifier"
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
        
        section_role_id, section_category_id = await self.db.get_fetchone("SELECT RoleId, CategoryId FROM 'Sections' WHERE GuildId=? AND Identifier=?", (interaction.guild_id, identifier.lower()))
        section_role = interaction.guild.get_role(section_role_id)
        section_category : CategoryChannel = interaction.guild.get_channel(section_category_id)
        
        try:
            for channel in section_category.channels:
                await channel.delete()

            await section_role.delete()
            await section_category.delete()
        except:
            pass

        await self.db.request(
            """Delete FROM 'Sections' WHERE GuildId=? AND Identifier=?""", (interaction.guild_id, identifier.lower()),
        )

        await interaction.edit_original_message(embed=success_embed, view=None)
    

    @application_checks.has_permissions(administrator=True)
    @section.subcommand(name="list")
    async def section_list(self, interaction : Interaction):
        identifiers = await self.db.get_fetchall("SELECT Identifier FROM Sections WHERE GuildId=?", (interaction.guild_id,))
        subjects = [f"- Section {identifier[0].upper()}" for identifier in identifiers]

        list_embed = Embed(
            title=f"List of Sections in {interaction.guild.name}",
            description="\n".join(subjects) if subjects else "No Section yet",
            color=Color.blue()
        )
        list_embed.set_thumbnail(url=interaction.guild.icon)
        await interaction.response.send_message(embed=list_embed)


def setup(client: Bot):
    client.add_cog(Sections(client))
