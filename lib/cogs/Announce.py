import discord
from discord.ext.commands import Cog, has_guild_permissions, bot_has_guild_permissions
from discord.commands import SlashCommandGroup, option
from discord.channel import TextChannel
from discord.embeds import Embed

from lib.bot import Bot
from lib.context import CustomContext


class Announce(Cog):
    def __init__(self, bot):
        self.bot: Bot = bot

    announce = SlashCommandGroup('announcements')

    @staticmethod
    def get_news(channels: list[TextChannel]) -> TextChannel | None:
        for ch in channels:
            if ch.is_news():
                return ch

    @announce.command(name="enable", description='Enable bot announcements')
    @option(name='channel',
            type=discord.TextChannel,
            description='Bot Announcements Channel',
            required=False)
    @has_guild_permissions(manage_guild=True)
    @bot_has_guild_permissions(send_messages=True)
    async def announce_enable(self, ctx: CustomContext, channel: discord.TextChannel | None):
        channel = channel if channel is not None else self.get_news(ctx.guild.text_channels)
        if channel is None:
            return await ctx.respond(Embed(title='Channel Not Found', description=f">>> Can't find an announcements channel to enable", colour=0xff0000))
        if not channel.permissions_for(await ctx.guild.fetch_member(self.bot.user.id)).send_messages:
            return await ctx.respond(Embed(title='Missing Permissions', description=f">>> I can't send messages in channel: {channel.name} ({channel.id})"))
        self.bot.db.execute("""UPDATE guilds SET a_id=? WHERE id=?""", channel.id, ctx.guild.id)
        await ctx.respond(embed=Embed(title='Update Announcments', description=f">>> Successfully Enabled Announcments in {channel.mention} ({channel.id})", colour=0x00ff00))

    @announce.command(name='disable', description='Disable bot announcements')
    @has_guild_permissions(manage_guild=True)
    async def announce_disable(self, ctx: CustomContext):
        self.bot.db.execute("""UPDATE guilds SET a_id=?""")


def setup(bot):
    bot.add_cog(Announce(bot))
