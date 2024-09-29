import os
import nextcord

from config import DISCORD_TOKEN
from nextcord import Intents, Interaction
from nextcord.ext.commands import Bot, errors, Context
from nextcord.ext.application_checks import errors as application_errors
from utils.db import DB


class Client(Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.loop.create_task(self.get_ready())

    async def get_ready(self): 
        self.db = DB()
        await self.db.load_db("main.db")
        self.load_extensions()

    def load_extensions(self) -> None:
        print("---------[Loading]---------")
        loaded = []
        for filename in os.listdir("./cogs"):
            if filename.endswith(".py"):
                self.load_extension(f"cogs.{filename[:-3]}")
                print(f"[System]: {filename[:-3]} cog loaded.")
                loaded.append(filename[:-3])
        print("---------------------------")
        return loaded

    def unload_extensions(self) -> None:
        print("--------[Unloading]--------")
        for filename in os.listdir("./cogs"):
            if filename.endswith(".py"):
                self.unload_extension(f"cogs.{filename[:-3]}")
                print(f"[System]: {filename[:-3]} cog unloaded.")
        print("---------------------------")

    async def on_ready(self):
        print(f"Ready ! connected as {self.user.name}")


    async def on_application_command_error(
        self, interaction: Interaction, error: Exception
    ) -> None:
        if isinstance(error, application_errors.ApplicationMissingRole):
            role = interaction.guild.get_role(int(error.missing_role))
            await interaction.send(
                f"The role {role.mention} is required to use this command.",
                ephemeral=True,
            )
            return
        
        if isinstance(error, application_errors.ApplicationMissingAnyRole):
            roles = [interaction.guild.get_role(int(role)) for role in error.missing_roles]
            await interaction.send(
                f"In order to use this command, it is required to have atleast **one** of these roles: {', '.join([role.mention for role in roles])}",
                ephemeral=True,
            )
            return

        elif isinstance(error, application_errors.ApplicationMissingPermissions):
            permissions = error.missing_permissions
            await interaction.send(
                f"the permission{'s' if len(permissions) > 1 else ''}: **{', '.join(permissions)}**. {'are' if len(permissions) > 1 else 'is'} required to use this command.",
                ephemeral=True,
            )
            return
        
        raise error




client = Client(
    "=", intents=Intents(messages=True, guilds=True, members=True, message_content=True, invites=True)
)

if __name__ == "__main__":
    client.run(DISCORD_TOKEN)
