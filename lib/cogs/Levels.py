from discord.ext.commands import Cog
from discord.commands import slash_command

from lib.bot import Bot
from lib.context import CustomContext


class Levels(Cog):
    def __init__(self, bot):
        self.bot: Bot = bot

    @slash_command(name="command_name")
    async def command_name(self, ctx: CustomContext):
        pass


def setup(bot):
    bot.add_cog(Levels(bot))
