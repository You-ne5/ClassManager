from nextcord.ext.commands import Bot, Cog
from nextcord.ext import application_checks
from nextcord import (
    Embed,
    Interaction,
    Message,
    CategoryChannel,
    Member,
    Color,
    PermissionOverwrite,
    slash_command
    
)

from config import EMBED_COLOR
from utils.views import Confirm
from utils.functions import get_constant_id
from utils.db import DB

class Groups(Cog):
    def __init__(self, client: Bot) -> None:
        self.client = client


    async def connect_db(self):
        self.db = DB()
        await self.db.load_db("main.db")


    @Cog.listener()
    async def on_ready(self):
        await self.connect_db()
        return
    
    @slash_command(name="group")
    async def group(self, interaction : Interaction):
        return
    
    @group.subcommand(name="add", description="Creates a group, with a role and a specific category")
    async def group_add(
        self, 
        interaction : Interaction, 
        group_number : int,
        section_id : str
        ):

        section_id = section_id.lower()

        confirm_embed = Embed(
            title="Are you sure of these informations?",
            description=f"``group number:`` {str(group_number)}",
            colour=EMBED_COLOR,
        )
        fail_embed = Embed(color=EMBED_COLOR)
        success_embed = Embed(
            title="group created !",
            description=f"The group '{group_number}' has been created !",
            color=EMBED_COLOR,
        )

        existing_numbers = await self.db.get_fetchall("SELECT Number FROM 'Groups' WHERE GuildId=?", (interaction.guild_id,))
        existing_numbers = [name[0] for name in existing_numbers]

        if group_number in existing_numbers:
            fail_embed.title = "Group already exists"
            fail_embed.description = f"The Group Number {group_number} already exists, please try again using another number"
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
        
        group_role = await interaction.guild.create_role(name=f"group {group_number}")

        category_perms = {
            interaction.guild.default_role : PermissionOverwrite(view_channel=False, send_messages=False),
            group_role : PermissionOverwrite(view_channel=True, send_messages=True)
        }

        section_category_id = await self.db.get_fetchone("SELECT CategoryId FROM Sections WHERE GuildId=? AND Identifier=?", (interaction.guild_id, section_id,))
        if not section_category_id:
            await interaction.response.send_message(content=f"Section '{section_id}' not found, please choose a valid id", ephemeral=True)
            return

        section_category = interaction.guild.get_channel(section_category_id[0])
        group_channel = await section_category.create_text_channel(
            name=f"Group {group_number}",
            overwrites=category_perms
            )

        await self.db.request(
            """INSERT INTO 'Groups'('GuildId', 'Number', 'SectionId', 'RoleId', 'ChannelId') VALUES(?,?,?,?,?)""",
            (
                interaction.guild_id,
                group_number,
                section_id,
                group_role.id,
                group_channel.id
            ),
        )

        await interaction.edit_original_message(embed=success_embed, view=None)


    @group.subcommand(name="remove", description="Removes a Group")
    async def group_remove(
        self, 
        interaction : Interaction, 
        group_number : int
        ):
        confirm_embed = Embed(
            title="Are you sure You want to delete this group?",
            description=f"``group :`` {group_number}",
            colour=EMBED_COLOR,
        )
        fail_embed = Embed(color=EMBED_COLOR)
        success_embed = Embed(
            title="Section Deleted !",
            description=f"The group {group_number} has been deleted !",
            color=EMBED_COLOR,
        )

        groups_numbers = await self.db.get_fetchall("SELECT Number FROM 'Groups' WHERE GuildId=?", (interaction.guild_id,))
        groups_numbers = [name[0] for name in groups_numbers]

        if not group_number in groups_numbers:
            fail_embed.title = "Group doesn't exist!"
            fail_embed.description = f"The Group {group_number} does not exist, please try again using another number"
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
        
        group_role_id, group_channel_id = await self.db.get_fetchone("SELECT RoleId, ChannelId FROM 'Groups' WHERE GuildId=? AND Number=?", (interaction.guild_id, group_number))
        print(group_role_id)
        group_role = interaction.guild.get_role(group_role_id)
        group_channel = interaction.guild.get_channel(group_channel_id)
        
        try:
            await group_role.delete()
            await group_channel.delete()
        except:
            pass

        await self.db.request(
            """Delete FROM 'Groups' WHERE GuildId=? AND Number=?""", (interaction.guild_id, group_number),
        )

        await interaction.edit_original_message(embed=success_embed, view=None)
    

    @application_checks.has_permissions(administrator=True)
    @group.subcommand(name="list")
    async def group_list(self, interaction : Interaction):
        groups_numbers = await self.db.get_fetchall("SELECT Number FROM Groups WHERE GuildId=?", (interaction.guild_id,))
        groups = [f"- Group {number[0]}" for number in groups_numbers]

        list_embed = Embed(
            title=f"List of Groups in {interaction.guild.name}",
            description="\n".join(groups) if groups else "No group yet",
            color=Color.blue()
        )
        list_embed.set_thumbnail(url=interaction.guild.icon)
        await interaction.response.send_message(embed=list_embed)


def setup(client: Bot):
    client.add_cog(Groups(client))
