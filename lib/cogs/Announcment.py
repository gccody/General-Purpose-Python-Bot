from typing import Optional

import discord
from discord import app_commands, Interaction
from discord.channel import TextChannel
from discord.embeds import Embed
from discord.ext.commands import Cog, has_guild_permissions, bot_has_guild_permissions

from lib.bot import Bot


class Announce(Cog):
    announce = app_commands.Group(name='announcements', description='Enable and disable announcements')

    def __init__(self, bot):
        self.bot: Bot = bot

    @staticmethod
    def get_news(channels: list[TextChannel]) -> TextChannel | None:
        for ch in channels:
            if ch.is_news():
                return ch

    @announce.command(name="enable", description='Enable bot announcements')
    @app_commands.describe(channel='Bot Announcements Channel')
    @has_guild_permissions(manage_guild=True)
    @bot_has_guild_permissions(send_messages=True)
    async def announce_enable(self, ctx: Interaction, channel: Optional[discord.TextChannel]):
        channel = channel if channel is not None else self.get_news(ctx.guild.text_channels)
        if channel is None:
            return await ctx.response.send_message(
                Embed(title=f">>> Can't find an announcements channel to enable", colour=0xff0000))
        if not channel.permissions_for(await ctx.guild.fetch_member(self.bot.user.id)).send_messages:
            return await ctx.response.send_message(
                Embed(title=f">>> I can't send messages in channel: {channel.name} ({channel.id})", colour=0xff0000))
        self.bot.db.update.guilds(where=f'id={ctx.guild_id}', set_data={'a_id': channel.id})
        await self.bot.send(ctx, embed=Embed(
            title=f">>> Successfully Enabled Announcements in {channel.mention} ({channel.id})"))

    @announce.command(name='disable', description='Disable bot announcements')
    @has_guild_permissions(manage_guild=True)
    async def announce_disable(self, ctx: Interaction):
        self.bot.db.update.guilds(where=f'id={ctx.guild_id}', set_data={'a_id': None})
        await self.bot.send(ctx,
                            embed=Embed(title=f">>> Successfully Disabled Announcements"))


async def setup(bot):
    await bot.add_cog(Announce(bot))
