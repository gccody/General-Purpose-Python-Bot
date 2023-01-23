from discord.ext.commands import Cog
from discord import app_commands, Interaction

from lib.bot import Bot


class Levels(Cog):
    def __init__(self, bot):
        self.bot: Bot = bot

    @app_commands.command(name="level")
    async def level(self, ctx: Interaction):
        pass


async def setup(bot):
    await bot.add_cog(Levels(bot))
