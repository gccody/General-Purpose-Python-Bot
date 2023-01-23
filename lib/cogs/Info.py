import os
from typing import Optional

import discord
import psutil
from discord.embeds import Embed
from discord.ext.commands import Cog
from discord import app_commands
from discord.guild import Guild
from discord.interactions import Interaction

from lib.bot import Bot


class Info(Cog):
    bott = app_commands.Group(name='bot', description='Get the status of the bot')
    server = app_commands.Group(name='server', description='Get the status of the server')

    def __init__(self, bot: Bot):
        self.bot: Bot = bot

    @bott.command(name="status", description="Get the current status of the bot")
    async def status(self, ctx: Interaction):
        await ctx.response.defer()
        embed: Embed = Embed()
        python_process = psutil.Process(os.getpid())
        owner = await self.bot.fetch_user(self.bot.owner_id)
        # embed.set_author(name=f"{nickname if nickname else self.bot.user.display_name}#{self.bot.user.discriminator}",
        #                  icon_url="https://i.imgur.com/QMykWjw.png")
        embed.description = f"""
**SHARD:** `{ctx.guild.shard_id + 1}/{self.bot.shard_count}` **LATENCY:** `{round(self.bot.get_shard(ctx.guild.shard_id).latency, 2)}`
**RAM:** `{round(python_process.memory_info()[0] / 2. ** 30, 2)} Gb` **CPU:** `{await self.bot.cpu_percent(1)}%`
**OWNER:** `{owner.display_name}#{owner.discriminator}`
**SERVERS:** `{len(self.bot.guilds)}` **MEMBERS:** `{len(list(self.bot.get_all_members()))}` **CHANNELS:** `{len(list(self.bot.get_all_channels()))}`
"""
        # embed.add_field(name='Total commands', value=f"`{len(self.bot.application_commands)}`", inline=False)
        await self.bot.send(ctx, embed=embed)

    @server.command(name='info', description='Get the info of the current server')
    async def server_info(self, ctx: Interaction):
        await ctx.response.defer()
        guild: Guild = ctx.guild
        embed: Embed = Embed()

        # Get Emoji Info
        regular = 0
        animated = 0
        for emoji in guild.emojis:
            if emoji.animated:
                animated += 1
            else:
                regular += 1
        # Get Role Info
        roles_list = [role.mention for role in guild.roles if not role.is_bot_managed() and role.is_assignable()]
        roles = ' '.join(roles_list)
        roles_count = len(roles_list)

        # Get boost information
        boost_tier = guild.premium_tier
        filesize_limit = 100 if boost_tier == 3 else 50 if boost_tier == 2 else 8

        embed.add_field(name='___About___', value=f"""
**Name:** `{guild.name}`
**ID:** `{guild.id}`
**Owner:** `{guild.owner.display_name}#{guild.owner.discriminator} ({guild.owner_id})`
**Created At:** <t:{round(guild.created_at.timestamp())}:R>
**Members:** `{len([member for member in guild.members if not member.bot])}`
**Bots:** `{len([member for member in guild.members if member.bot])}`
**Banned:** `{len([entry async for entry in guild.bans(limit=5000)])}`
""", inline=False)
        embed.add_field(name='___Description___', value=guild.description if guild.description else 'None', inline=False)
#         embed.add_field(name='___Extras___', value=f"""
# **Verification Level:** {str(guild.verification_level).title()}
# **Upload Limit:** {filesize_limit} MB
# **Inactive Channel:** {guild.afk_channel.mention if guild.afk_channel else 'None'}
# **Inactive Timeout:** {guild.afk_timeout/60} minutes
# **System Messages Channel:** {guild.system_channel.mention if guild.system_channel else 'None'}
# **System Welcome Messages:** {"✅" if guild.system_channel_flags.join_notifications else ':x:'}
# **System Boost Messages:** {"✅" if guild.system_channel_flags.premium_subscriptions else ':x:'}
# **Default Notifications:** {"All Messages" if "all" in str(guild.default_notifications) else "Only Mentions"}
# **Explicit Media Content Filter:** {' '.join(str(guild.explicit_content_filter).split("_")).title()}
# **2FA Requirement:** {"✅" if guild.mfa_level else ":x:"}
# **Boost Bar** {"✅" if guild.premium_progress_bar_enabled else ":x:"}
# """, inline=False)
        embed.add_field(name='___Channels___', value=f"""
**Total:** `{len(guild.channels)}`
**Text:** `{len(guild.text_channels)}`
**Voice:** `{len(guild.voice_channels)}`
**Rules Channel:** `{guild.rules_channel.mention if guild.rules_channel else 'None'}`
""")
        embed.add_field(name='___Emojis___', value=f"""
**Regular:** `{regular}/{guild.emoji_limit}`
**Animated:** `{animated}/{guild.emoji_limit}`
**Total:** `{len(guild.emojis)}/{guild.emoji_limit}`
""")
        embed.add_field(name='___Boost___', value=f"""
**Level:** `{boost_tier}`
**Total:** `{guild.premium_subscription_count}`
**Boost Bar:** `{"✅" if guild.premium_progress_bar_enabled else "❌"}`
**Role:** `{guild.premium_subscriber_role.mention if guild.premium_subscriber_role else 'None'}`
""")
        embed.add_field(name=f'___Roles___ [{roles_count}]', value=f"""
{'None' if not roles_count else roles if len(roles) <=1024 else 'Too many to show'}
""", inline=False)

        # Add banner and icon if available
        if guild.banner:
            embed.set_image(url=guild.banner.url)
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)

        await self.bot.send(ctx, embed=embed)


async def setup(bot):
    await bot.add_cog(Info(bot))
