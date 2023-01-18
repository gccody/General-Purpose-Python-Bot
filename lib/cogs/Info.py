from discord.ext.commands import Cog
from discord.ext.commands import slash_command
from discord.commands import SlashCommandGroup
from discord.embeds import Embed

from lib.bot import Bot
from lib.context import CustomContext


class Info(Cog):
    def __init__(self, bot: Bot):
        self.bot: Bot = bot

    one = SlashCommandGroup('one')
    two = one.create_subgroup('two')

    @slash_command(name="status", description="Get the current status of the bot")
    async def status(self, ctx: CustomContext):
        embed: Embed = Embed(title="Bot status")
        embed.add_field(name='Shard latency', value=f"{self.bot.get_shard(ctx.guild.shard_id).latency}")
        await ctx.respond(embed=embed)

    @two.command(name='test')
    async def two_layer_test(self, ctx: CustomContext):
        await ctx.respond("Hello!")


def setup(bot):
    bot.add_cog(Info(bot))
