from typing import cast

from discord.app_commands import Command
from discord.app_commands.errors import CommandInvokeError
from discord.ext.commands import Cog
from discord.interactions import Interaction

from lib.bot import Bot
from lib.errors import BotNotReady


class Handler(Cog):
    def __init__(self, bot):
        self.bot: Bot = bot

    # @Cog.listener()
    # async def on_interaction(self, ctx: Interaction):
    #     if isinstance(ctx.command, Command):
    #         raise CommandInvokeError("Tessting")
        # if isinstance(ctx.command, discord.app_commands.Command):
        #     name_list, options = self.bot.get_name(ctx.data, [])
        #     name = " ".join(name_list)
            # self.bot.db.run(f"""INSERT INTO commands VALUES (?,?,?,?,?)""", name, ctx.guild_id,
            #                     ctx.user.id, json.dumps(options), datetime.now().timestamp())


async def setup(bot):
    await bot.add_cog(Handler(bot))
