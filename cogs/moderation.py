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
    CategoryChannel,
    PermissionOverwrite
)

from config import EMBED_COLOR
from utils.views import HelpView, HelpPanel, Confirm
from utils.functions import get_hac_id, message_verif, create_constant, get_help_category_id, get_lessons_category_id
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
        return


    @slash_command(name="subject")
    async def subject(self, interaction: Interaction):
        return


    @Cog.listener()
    async def on_interaction(self, interaction : Interaction):
        if not interaction.data.get("custom_id") == "help_subject":
            return
        
        help_category : CategoryChannel = interaction.guild.get_channel(await get_help_category_id(interaction.guild_id))
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
            description=f"Subject '{subject_emoji}{subject_name}' has been added !",
            color=EMBED_COLOR,
        )

        existing_names = await self.db.get_fetchall("SELECT Name FROM 'Subjects' WHERE GuildId=?", (interaction.guild_id,))
        existing_names = [name[0].lower() for name in existing_names]

        if subject_name.lower() in existing_names:
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
            """INSERT INTO 'Subjects'('GuildId', 'Name', 'Emoji') VALUES(?,?,?)""",
            (
                interaction.guild_id,
                subject_name.lower(),
                subject_emoji,
            ),
        )
        lessons_category = interaction.guild.get_channel(await get_lessons_category_id(interaction.guild_id))
        await lessons_category.create_text_channel(name=f"{subject_emoji} {subject_name.lower()}")
        await interaction.edit_original_message(embed=success_embed, view=None)


    @application_checks.has_permissions(administrator=True)
    @subject.subcommand(name="remove")
    async def subject_remove(
        self,
        interaction: Interaction,
        subject_name: str = SlashOption(name="name", description="the subject's name"),
    ):
        confirm_embed = Embed(
            title="Are you sure you want to remove this subject?",
            description=f"``Subject name:`` {subject_name}",
            colour=EMBED_COLOR,
        )
        fail_embed = Embed(color=EMBED_COLOR)
        success_embed = Embed(
            title="Subject Removed",
            description=f"Subject '{subject_name}' has been removed !",
            color=EMBED_COLOR,
        )

        existing_names = await self.db.get_fetchall("SELECT Name FROM 'Subjects' WHERE GuildId=?", (interaction.guild_id,))
        existing_names = [name[0].lower() for name in existing_names]

        if not subject_name.lower() in existing_names:
            fail_embed.title = "Subject does not exist"
            fail_embed.description = f"The subject '{subject_name}' Does not exist, please verify the subject name and try again"
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
            "DELETE FROM Subjects WHERE GuildId=? AND Name=?",
            (
                interaction.guild_id,
                subject_name.lower(),
            ),
        )

        lessons_category = interaction.guild.get_channel(await get_lessons_category_id(interaction.guild_id))
        try:
            for subject_channel in lessons_category.channels:
                if subject_name.lower() in subject_channel.name:
                    await subject_channel.delete()
                    break
        except:
            pass
        await interaction.edit_original_message(embed=success_embed, view=None)


    @application_checks.has_permissions(administrator=True)
    @subject.subcommand(name="list")
    async def subject_list(self, interaction : Interaction):
        subjects = await self.db.get_fetchall("SELECT Name, Emoji FROM Subjects WHERE GuildId=?", (interaction.guild_id,))
        print(subjects)
        subjects = [f"- {subject_emoji} {subject_name}" for subject_name, subject_emoji in subjects]

        list_embed = Embed(
            title=f"List of Subjects in {interaction.guild.name}",
            description="\n".join(subjects) if subjects else "No subjects yet",
            color=Color.blue()
        )
        list_embed.set_thumbnail(url=interaction.guild.icon)
        await interaction.response.send_message(embed=list_embed)

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
        
        hac_id = await get_hac_id(guild_id=interaction.guild.id)
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


    @Cog.listener()
    async def on_message(self, message: Message):
        lessons_category_id = await get_lessons_category_id(message.guild.id)
        if message.author.id == self.client.user.id:
            return
        if (
            message.channel.category.id == lessons_category_id
            and not message_verif(message)
        ):
            await message.delete()
            await message.channel.send(
                content=f"{message.author.mention} Only messages containing links are allowed on this channel.",
                delete_after=6,
            )

    @application_checks.has_permissions(administrator=True)
    @slash_command(name="setup", description="Setup the bot")
    async def setup(self, interaction : Interaction):

        guild_id = interaction.guild_id
        constants_created = []
        return_embed = Embed(title="Bot has been Setup seccessfully", color=EMBED_COLOR)

        guild_constants = await self.db.get_fetchone("SELECT * FROM GuildsConstants WHERE GuildId=?", (guild_id,))

        if guild_constants:
            help_category = interaction.guild.get_channel(guild_constants[1])
            help_archive_category = interaction.guild.get_channel(guild_constants[2])
            lessons_category = interaction.guild.get_channel(guild_constants[3])
            exo_channel = interaction.guild.get_channel(guild_constants[4])
            announce_channel = interaction.guild.get_channel(guild_constants[5])

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
        else:
            await self.db.request("INSERT INTO 'GuildsConstants' VALUES (?,?,?,?,?,?)", (guild_id, None, None, None, None, None))

            constants_created = ["HelpCategoryId", "HelpArchiveCategoryID", "LessonsCategoryId", "ExoChannelId", "AnnounceChannelId"]

            for constant_name in constants_created:
                await create_constant(interaction, constant_name)
        
        if constants_created:
            return_embed.description = "**Added Constants:**\n"
            return_embed.description += "\n".join([f"- {s}" for s in constants_created])
        await interaction.response.send_message(embed=return_embed)
    

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
        print(section_role_id)
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


def setup(client: Bot):
    client.add_cog(Moderation(client))
