from datetime import datetime, timedelta

import discord
from discord import SlashCommandGroup, option
from discord.embeds import Embed
from discord.errors import NotFound
from discord.ext.commands import Cog, has_guild_permissions, bot_has_guild_permissions, slash_command
from discord.member import Member
from discord.permissions import Permissions
from discord.user import User

from lib.bot import Bot
from lib.context import CustomContext


class Mod(Cog):
    def __init__(self, bot: Bot):
        self.bot: Bot = bot
        self.days = {
            "Don't Delete Any": 0,
            "Previous 24 Hours": 1,
            "Previous 2 Days": 2,
            "Previous 3 Days": 3,
            "Previous 4 Days": 4,
            "Previous 5 Days": 5,
            "Previous 6 Days": 6,
            "Previous 7 Days": 7
        }

    ban = SlashCommandGroup("ban")
    massban = SlashCommandGroup("massban")
    mute = SlashCommandGroup("mute")
    massmute = SlashCommandGroup("massmute")
    purge = SlashCommandGroup("purge")
    p: Permissions

    def get_days(self, ctx: discord.AutocompleteContext):
        return [msg for msg, _ in self.days.items() if ctx.options['delete_messages'] in msg]

    @ban.command(name="add", description="Ban a user from guild")
    @option('member',
            discord.Member,
            description="Member to ban",
            required=True)
    @option('delete_messages',
            str,
            description="How much of their recent messages to delete",
            required=False,
            default="Don't Delete Any",
            autocomplete=get_days)
    @option('reason',
            str,
            description="Reason to ban member",
            required=False,
            default="No reason provided")
    @has_guild_permissions(ban_members=True)
    @bot_has_guild_permissions(ban_members=True)
    async def ban_add(self, ctx: CustomContext, member: discord.Member, delete_messages: str, reason: str):

        # Check if the member is a member
        # Check if the members role position is lower than your role position
        # Check if the member isn't the owner
        if isinstance(member,
                      Member) and member.top_role.position < ctx.user.top_role.position or not ctx.guild.owner == ctx.user:
            return await ctx.respond(embed=Embed(title=">>> You need a role higher then the user you are trying to ban",
                                                 colour=0xff0000))

        # Check if the targeted member is the guild owner
        elif member == ctx.guild.owner:
            return await ctx.respond(
                embed=Embed(title=":x: | You can not ban the owner of the server",
                            colour=0xff0000))

        # Check if the targeted member is the current bot
        elif member == self.bot.user:
            return await ctx.respond(
                embed=Embed(title=":x: | I can not ban myself", colour=0xff0000))

        # Member is a part of the guild
        if isinstance(member, Member):
            await member.ban(delete_message_days=self.days[delete_messages],
                             reason=f"{reason} | {ctx.user.display_name}#{ctx.user.discriminator}")

        # Member is not a part of the guild
        elif isinstance(member, User):
            await ctx.guild.ban(user=member, delete_message_days=self.days[delete_messages],
                                reason=f"{reason} | {ctx.user.display_name}#{ctx.user.discriminator}")
        self.bot.db.execute("""INSERT INTO bans VALUES (?,?,?,?,?)""", ctx.guild_id, member.id, ctx.user.id, reason,
                            datetime.now().timestamp())
        embed = Embed(title=f"✅ | {member.display_name}#{member.discriminator} ({member.id}) has been banned")
        await ctx.respond(embed=embed)

    @ban.command(name="remove", description="Unban a user from guild")
    @option('member',
            discord.Member,
            description="Member to unban",
            required=True)
    @option('reason',
            str,
            description="Reason to unban member",
            required=False,
            default="No reason provided")
    @has_guild_permissions(ban_members=True)
    @bot_has_guild_permissions(ban_members=True)
    async def ban_remove(self, ctx: CustomContext, member: discord.Member, reason: str):
        try:  # Check if the member is already banned
            await ctx.guild.fetch_ban(member)
        except NotFound:  # Not banned so move on
            return await ctx.respond(
                embed=Embed(title=f":x: | That member is already unbanned", colour=0xff0000))

        # Member is a part of the guild
        if isinstance(member, Member):
            await member.unban(reason=reason)
        # Member is not part of the guild
        elif isinstance(member, User):
            await ctx.guild.unban(user=member, reason=reason)
        self.bot.db.execute("""DELETE FROM bans WHERE guild_id=? AND user_id=? """, ctx.guild_id, member.id)
        await ctx.respond(
            embed=Embed(title=f"✅ | {member.display_name}#{member.discriminator} ({member.id}) has been unbanned"))

    @massban.command(name="add", description="Mass ban users from guild")
    @option('members',
            str,
            description="Space separated list of member ids",
            required=True)
    @option('delete_messages',
            str,
            description="How much of their recent messages to delete",
            required=False,
            default="Don't Delete Any",
            autocomplete=get_days)
    @option('reason',
            str,
            description="Reason to ban members",
            required=False,
            default="No reason provided")
    @has_guild_permissions(ban_members=True)
    @bot_has_guild_permissions(ban_members=True)
    async def massban_add(self, ctx: CustomContext, str_members: str, delete_messages: str, reason: str):
        failed = []
        success = []
        banned_already = []
        for id in str_members.split(" "):  # Iterate through all the member ids
            try:  # Try to fetch the member
                member = await ctx.guild.fetch_member(int(id))
            except NotFound:  # Member isn't found the fail and move to next id
                failed.append(id)
                continue

            try:  # Check if the user is already banned
                await ctx.guild.fetch_ban(user=member)
                banned_already.append(f"{member.display_name}#{member.discriminator} ({id})")
                continue
            except NotFound:  # if no ban then we good
                pass

            # Check that the member is available to ban and fail if not
            if member == self.bot.user or member == ctx.guild.owner or member.top_role.position < ctx.user.top_role.position or not ctx.guild.owner == ctx.user:
                failed.append(f"{member.display_name}#{member.discriminator} ({id})")
                continue
            await member.ban(delete_message_days=self.days[delete_messages],
                             reason=f"{reason} | {ctx.user.display_name}#{ctx.user.discriminator}")
            self.bot.db.execute("""INSERT INTO bans VALUES (?,?,?,?,?)""", ctx.guild_id, member.id, ctx.user.id, reason,
                                datetime.now().timestamp())
            success.append(f"{member.display_name}#{member.discriminator} ({id})")
        embed = Embed()
        s_users = "\n".join(success)
        b_users = "\n".join(banned_already)
        f_users = "\n".join(failed)
        embed.add_field(name='Succeeded', value=f">>> {s_users}" if s_users != "" else "None", inline=True)
        embed.add_field(name='Banned Already', value=f">>> {b_users}" if b_users != "" else "None", inline=True)
        embed.add_field(name='Failed', value=f">>> {f_users}" if f_users != "" else "None", inline=True)
        await ctx.respond(embed=embed)

    @massban.command(name='remove', description='Mass unban users from a guild')
    @option('members',
            str,
            description="Space separated list of member ids",
            required=True)
    @option('delete_messages',
            str,
            description="How much of their recent messages to delete",
            required=False,
            default="Don't Delete Any",
            autocomplete=get_days)
    @option('reason',
            str,
            description="Reason to ban members",
            required=False,
            default="No reason provided")
    @has_guild_permissions(ban_members=True)
    @bot_has_guild_permissions(ban_members=True)
    async def massban_remove(self, ctx: CustomContext, str_members: str, delete_messages: str, reason: str):
        failed = []
        success = []
        unbanned_already = []
        for id in str_members.split(" "):  # Iterate through all the ids

            try:  # try to fetch the member and if u can't then fail and move to the next id
                member = await ctx.guild.fetch_member(int(id))
            except NotFound:
                failed.append(id)
                continue

            try:  # check if member is banned
                await ctx.guild.fetch_ban(user=member)
            except NotFound:  # Member isn't banned so save and move on
                unbanned_already.append(f"{member.display_name}#{member.discriminator} ({id})")
                continue

            await member.unban(reason=f"{reason} | {ctx.user.display_name}#{ctx.user.discriminator}")
            self.bot.db.execute("""DELETE FROM bans WHERE guild_id=? AND user_id=? """, ctx.guild_id, member.id)
            success.append(f"{member.display_name}#{member.discriminator} ({id})")
        embed = Embed()
        s_users = "\n".join(success)
        b_users = "\n".join(unbanned_already)
        f_users = "\n".join(failed)
        embed.add_field(name='Succeeded', value=f">>> {s_users}" if s_users != "" else "None", inline=True)
        embed.add_field(name='Banned Already', value=f">>> {b_users}" if b_users != "" else "None", inline=True)
        embed.add_field(name='Failed', value=f">>> {f_users}" if f_users != "" else "None", inline=True)
        await ctx.respond(embed=embed)

    @slash_command(name="kick", description="Kick a user from guild")
    @option('member',
            discord.Member,
            description="Member to kick",
            required=True)
    @option('reason',
            str,
            description="Why are you kicking this member",
            required=False,
            default="No reason provided")
    @has_guild_permissions(kick_members=True)
    @bot_has_guild_permissions(kick_members=True)
    async def kick(self, ctx: CustomContext, member: discord.Member, reason: str | None):
        if member.top_role.position < ctx.user.top_role.position or not ctx.guild.owner == ctx.user:
            return await ctx.respond(
                embed=Embed(title=":x: | You need a role higher then the user you are trying to kick",
                            colour=0xff0000))
        elif member == ctx.guild.owner:
            return await ctx.respond(
                embed=Embed(title=":x: | You can not kick the owner of the server",
                            colour=0xff0000))
        elif member == self.bot.user:
            return await ctx.respond(
                embed=Embed(title=":x: | I can not kick myself", colour=0xff0000))

        await member.kick(reason=f"{reason} | {ctx.user.display_name}#{ctx.user.discriminator}")
        embed = Embed(title=f"✅ | {member.display_name}#{member.discriminator} ({member.id}) has been kicked")
        embed.set_author(name=ctx.user)
        await ctx.respond(embed=embed)

    @slash_command(name='masskick', description='Mass kick users from a guild')
    @option('members',
            str,
            description='Space separated list of member ids',
            required=True)
    @option('reason',
            str,
            description="Why are you kicking this member",
            required=False,
            default="No reason provided")
    async def masskick(self, ctx: CustomContext, members: str, reason: str):
        success = []
        fail = []
        for id in members.split(" "):
            try:
                member = await ctx.guild.fetch_member(int(id))
            except NotFound:
                fail.append(id)
                continue

            if member.top_role.position < ctx.user.top_role.position or not ctx.guild.owner == ctx.user:
                fail.append(f"{member.display_name}#{member.discriminator}")
            elif member == ctx.guild.owner:
                fail.append(f"{member.display_name}#{member.discriminator}")
            elif member == self.bot.user:
                fail.append(f"{member.display_name}#{member.discriminator}")

            await member.kick(reason=f"{reason} | {ctx.user.display_name}#{ctx.user.discriminator}")
            success.append(f"{member.display_name}#{member.discriminator}")

        embed = Embed()
        s_users = "\n".join(success)
        f_users = "\n".join(fail)
        embed.add_field(name='Succeeded', value=f">>> {s_users}" if s_users != "" else "None", inline=True)
        embed.add_field(name='Failed', value=f">>> {f_users}" if f_users != "" else "None", inline=True)
        await ctx.respond(embed=embed)

    @mute.command(name="add", description="Mute a user in the guild")
    @option('member',
            discord.Member,
            description="Member to mute",
            required=True)
    @option('minutes',
            float,
            min_value=.1,
            description="Minutes to mute",
            required=True)
    @option('reason',
            str,
            description="Reason to mute member",
            required=False,
            default="No reason provided")
    @has_guild_permissions(moderate_members=True)
    @bot_has_guild_permissions(moderate_members=True)
    async def mute_add(self, ctx: CustomContext, member: discord.Member, minutes: float, reason: str):

        # Check if the member is a member
        # Check if the members role position is lower than your role position
        # Check if the member isn't the owner
        if isinstance(member,
                      Member) and member.top_role.position < ctx.user.top_role.position or not ctx.guild.owner == ctx.user:
            return await ctx.respond(
                embed=Embed(title=":x: | You need a role higher then the user you are trying to mute",
                            colour=0xff0000))

        # Check if the targeted member is the guild owner
        elif member == ctx.guild.owner:
            return await ctx.respond(
                embed=Embed(title=":x: | You can not mute the owner of the server",
                            colour=0xff0000))

        # Check if the targeted member is the current bot
        elif member == self.bot.user:
            return await ctx.respond(
                embed=Embed(title=":x: | I can not mute myself", colour=0xff0000))

        # Member is a part of the guild
        if isinstance(member, Member):
            await member.timeout(until=datetime.now() + timedelta(minutes=minutes),
                                 reason=f"{reason} | {ctx.user.display_name}#{ctx.user.discriminator}")

        # Member is not a part of the guild
        elif isinstance(member, User):
            return await ctx.respond(Embed(title=':x: | I can not mute a member not in the server',
                                           colour=0xff0000))
        embed = Embed(title=f"✅ | {member.display_name}#{member.discriminator} ({member.id}) has been muted")
        await ctx.respond(embed=embed)

    @mute.command(name="remove", description="unmute a user from guild")
    @option('member',
            discord.Member,
            description="Member to unmute",
            required=True)
    @option('reason',
            str,
            description="Reason to unmute member",
            required=False,
            default="No reason provided")
    @has_guild_permissions(moderate_members=True)
    @bot_has_guild_permissions(moderate_members=True)
    async def mute_remove(self, ctx: CustomContext, member: discord.Member, reason: str):
        if not member.timed_out:
            return await ctx.respond(
                embed=Embed(title=f":x: | That member is already unmuted", colour=0xff0000))

        # Member is a part of the guild
        if isinstance(member, Member):
            await member.timeout(until=datetime.now(), reason=reason)
        # Member is not part of the guild
        elif isinstance(member, User):
            return await ctx.respond(
                embed=Embed(title=f":x: | I can not unmute a member not in the server"))
        await ctx.respond(
            embed=Embed(title=f"✅ | {member.display_name}#{member.discriminator} ({member.id}) has been unmuted"))

    @massmute.command(name="add", description="Mass mute users from guild")
    @option('members',
            str,
            description="Space separated list of member ids",
            required=True)
    @option('minutes',
            float,
            min_value=.1,
            description="Minutes to mute",
            required=True)
    @option('reason',
            str,
            description="Reason to mute members",
            required=False,
            default="No reason provided")
    @has_guild_permissions(moderate_members=True)
    @bot_has_guild_permissions(moderate_members=True)
    async def massmute_add(self, ctx: CustomContext, str_members: str, minutes: float, reason: str):
        failed = []
        success = []
        muted_already = []
        for id in str_members.split(" "):  # Iterate through all the member ids
            try:  # Try to fetch the member
                member = await ctx.guild.fetch_member(int(id))
            except NotFound:  # Member isn't found the fail and move to next id
                failed.append(id)
                continue

            if member.timed_out:  # Check if the user is already muted
                muted_already.append(f"{member.display_name}#{member.discriminator} ({id})")
                continue

            # Check that the member is available to ban and fail if not
            if member == self.bot.user or member == ctx.guild.owner or member.top_role.position < ctx.user.top_role.position or not ctx.guild.owner == ctx.user:
                failed.append(f"{member.display_name}#{member.discriminator} ({id})")
                continue
            await member.timeout(until=datetime.now() + timedelta(minutes=minutes),
                                 reason=f"{reason} | {ctx.user.display_name}#{ctx.user.discriminator}")
            success.append(f"{member.display_name}#{member.discriminator} ({id})")
        embed = Embed()
        s_users = "\n".join(success)
        m_users = "\n".join(muted_already)
        f_users = "\n".join(failed)
        embed.add_field(name='Succeeded', value=f">>> {s_users}" if s_users != "" else "None", inline=True)
        embed.add_field(name='Muted Already', value=f">>> {m_users}" if m_users != "" else "None", inline=True)
        embed.add_field(name='Failed', value=f">>> {f_users}" if f_users != "" else "None", inline=True)
        await ctx.respond(embed=embed)

    @massmute.command(name='remove', description='Mass unmute users from a guild')
    @option('members',
            str,
            description="Space separated list of member ids",
            required=True)
    @option('reason',
            str,
            description="Reason to unmute members",
            required=False,
            default="No reason provided")
    @has_guild_permissions(moderate_members=True)
    @bot_has_guild_permissions(moderate_members=True)
    async def massmute_remove(self, ctx: CustomContext, str_members: str, reason: str):
        failed = []
        success = []
        unmutted_alread = []
        for id in str_members.split(" "):  # Iterate through all the ids

            try:  # try to fetch the member and if u can't then fail and move to the next id
                member = await ctx.guild.fetch_member(int(id))
            except NotFound:
                failed.append(id)
                continue

            if not member.timed_out:  # check if member is muted
                unmutted_alread.append(f"{member.display_name}#{member.discriminator} ({id})")
                continue

            # Check that the member is available to unmute and fail if not
            if member == self.bot.user or member == ctx.guild.owner or member.top_role.position < ctx.user.top_role.position or not ctx.guild.owner == ctx.user:
                failed.append(f"{member.display_name}#{member.discriminator} ({id})")
                continue

            await member.timeout(until=datetime.now(),
                                 reason=f"{reason} | {ctx.user.display_name}#{ctx.user.discriminator}")
            success.append(f"{member.display_name}#{member.discriminator} ({id})")
        embed = Embed()
        s_users = "\n".join(success)
        m_users = "\n".join(unmutted_alread)
        f_users = "\n".join(failed)
        embed.add_field(name='Succeeded', value=f">>> {s_users}" if s_users != "" else "None", inline=True)
        embed.add_field(name='Muted Already', value=f">>> {m_users}" if m_users != "" else "None", inline=True)
        embed.add_field(name='Failed', value=f">>> {f_users}" if f_users != "" else "None", inline=True)

    @slash_command(name='report', description='Report a user')
    @option('member',
            discord.Member,
            description='Member to report',
            required=True)
    @option('reason',
            str,
            description='Reason to report the member',
            required=True)
    async def report(self, ctx: CustomContext, member: discord.Member, reason: str):
        pass

    @purge.command(name='all', description='Removes all messages')
    @option('limit',
            int,
            min_value=1,
            max_value=1000,
            default=100,
            description='Amount of messages to purge 1-1000. Default 100',
            required=False)
    @option('reason',
            str,
            description='Reason for deleting messages',
            required=False,
            default="No reason provided")
    @has_guild_permissions(manage_messages=True, read_message_history=True)
    @bot_has_guild_permissions(manage_messages=True, read_message_history=True)
    async def purge_all(self, ctx: CustomContext, limit: int, reason: str):
        await ctx.response.defer()
        messages = await ctx.channel.purge(limit=limit, before=discord.utils.snowflake_time(ctx.interaction.id),
                                           reason=reason)
        msg = await ctx.respond(
            embed=Embed(title=f'✅ | Successfully purged {len(messages)} messages'))
        await msg.delete(delay=3)

    @purge.command(name='bot', description='Removes all bot messages')
    @option('limit',
            int,
            min_value=1,
            max_value=1000,
            default=100,
            description='Amount of messages to purge 1-1000. Default 100',
            required=False)
    @option('reason',
            str,
            description='Reason for deleting messages',
            required=False,
            default="No reason provided")
    @has_guild_permissions(manage_messages=True, read_message_history=True)
    @bot_has_guild_permissions(manage_messages=True, read_message_history=True)
    async def purge_bot(self, ctx: CustomContext, limit: int, reason: str):
        await ctx.response.defer()
        messages = await ctx.channel.purge(limit=limit, before=discord.utils.snowflake_time(ctx.interaction.id),
                                           reason=reason, check=lambda message: message.author.bot)
        msg = await ctx.respond(
            embed=Embed(title=f'✅ | Successfully purged {len(messages)} bot messages'))
        await msg.delete(delay=3)

    @purge.command(name='user', description='Purge messages from a channel')
    @option('target',
            discord.Member,
            description='User to target',
            required=True)
    @option('limit',
            int,
            min_value=1,
            max_value=1000,
            default=100,
            description='Amount of messages to purge 1-1000. Default 100',
            required=False)
    @option('reason',
            str,
            description='Reason for deleting messages',
            required=False,
            default="No reason provided")
    @has_guild_permissions(manage_messages=True, read_message_history=True)
    @bot_has_guild_permissions(manage_messages=True, read_message_history=True)
    async def purge_user(self, ctx: CustomContext, target: discord.Member, limit: int, reason: str):
        await ctx.response.defer()
        messages = await ctx.channel.purge(limit=limit, before=discord.utils.snowflake_time(ctx.interaction.id),
                                           reason=reason, check=lambda message: message.user.id == target.id)
        msg = await ctx.respond(
            embed=Embed(
                title=f'✅ | Successfully purged {len(messages)} messages fro {target.display_name}#{target.discriminator}'))
        await msg.delete(delay=3)

    @purge.command(name='contains', description='Removes all messages containing a string')
    @option('string',
            str,
            description='String to target',
            required=True)
    @option('limit',
            int,
            min_value=1,
            max_value=1000,
            default=100,
            description='Amount of messages to purge 1-1000. Default 100',
            required=False)
    @option('reason',
            str,
            description='Reason for deleting messages',
            required=False,
            default="No reason provided")
    @has_guild_permissions(manage_messages=True, read_message_history=True)
    @bot_has_guild_permissions(manage_messages=True, read_message_history=True)
    async def purge_contains(self, ctx: CustomContext, string: str, limit: int, reason: str):
        await ctx.response.defer()
        messages = await ctx.channel.purge(limit=limit, before=discord.utils.snowflake_time(ctx.interaction.id),
                                           reason=reason,
                                           check=lambda message: string.lower() in message.content.lower())
        msg = await ctx.respond(
            embed=Embed(title=f'✅ | Successfully purged {len(messages)} messages containing {string}'))
        await msg.delete(delay=3)

    @purge.command(name='human', description='Removes all non-bot messages')
    @option('limit',
            int,
            min_value=1,
            max_value=1000,
            default=100,
            description='Amount of messages to purge 1-1000. Default 100',
            required=False)
    @option('reason',
            str,
            description='Reason for deleting messages',
            required=False,
            default="No reason provided")
    @has_guild_permissions(manage_messages=True, read_message_history=True)
    @bot_has_guild_permissions(manage_messages=True, read_message_history=True)
    async def purge_human(self, ctx: CustomContext, string: str, limit: int, reason: str):
        await ctx.response.defer()
        messages = await ctx.channel.purge(limit=limit, before=discord.utils.snowflake_time(ctx.interaction.id),
                                           reason=reason,
                                           check=lambda message: not message.author.bot)
        msg = await ctx.respond(
            embed=Embed(title=f'✅ | Successfully purged {len(messages)} human messages'))
        await msg.delete(delay=3)


def setup(bot):
    bot.add_cog(Mod(bot))
