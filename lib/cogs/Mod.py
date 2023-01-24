from datetime import datetime, timedelta
from typing import Optional

import discord
from discord import app_commands, Interaction
from discord.embeds import Embed
from discord.errors import NotFound
from discord.ext.commands import Cog, Greedy
from discord.member import Member
from discord.permissions import Permissions
from discord.user import User

from lib.bot import Bot


class Mod(Cog):
    ban = app_commands.Group(name='ban', description='Add/Remove bans')
    massban = app_commands.Group(name='massban', description='Add/Remove bans')
    mute = app_commands.Group(name='mute', description='Add/Remove mutes')
    massmute = app_commands.Group(name='massmute', description='Add/Remove mutes')
    purge = app_commands.Group(name='purge', description='Purge messages')

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

    p: Permissions

    @staticmethod
    async def get_days(_, current: str) -> list[app_commands.Choice[str]]:
        days = {
            "Don't Delete Any": 0,
            "Previous 24 Hours": 1,
            "Previous 2 Days": 2,
            "Previous 3 Days": 3,
            "Previous 4 Days": 4,
            "Previous 5 Days": 5,
            "Previous 6 Days": 6,
            "Previous 7 Days": 7
        }
        return [app_commands.Choice(name=msg, value=index) for msg, index in days.items() if current in msg]

    @ban.command(name="add", description="Ban a user from guild")
    @app_commands.describe(member='Member to ban', delete_messages='How much of their recent messages to delete',
                           reason='Reason to ban member')
    # @app_commands.autocomplete(delete_messages=get_days)
    @app_commands.checks.has_permissions(ban_members=True)
    @app_commands.checks.bot_has_permissions(ban_members=True)
    async def ban_add(self, ctx: Interaction, member: discord.Member, delete_messages: Optional[str],
                      reason: Optional[str] = "No Reason provided"):
        # Check if the member is a member
        # Check if the members role position is lower than your role position
        # Check if the member isn't the owner
        if isinstance(member,
                      Member) and member.top_role.position < ctx.user.top_role.position or not ctx.guild.owner == ctx.user:
            return await ctx.response.send_message(
                embed=Embed(title=">>> You need a role higher then the user you are trying to ban",
                            colour=0xff0000))

        # Check if the targeted member is the guild owner
        elif member == ctx.guild.owner:
            return await ctx.response.send_message(
                embed=Embed(title=":x: | You can not ban the owner of the server",
                            colour=0xff0000))

        # Check if the targeted member is the current bot
        elif member == self.bot.user:
            return await ctx.response.send_message(
                embed=Embed(title=":x: | I can not ban myself", colour=0xff0000))

        # Member is a part of the guild
        if isinstance(member, Member):
            await member.ban(delete_message_days=self.days[delete_messages] if delete_messages else 0,
                             reason=f"{reason} | {ctx.user.display_name}#{ctx.user.discriminator}")
        # Member is not a part of the guild
        elif isinstance(member, User):
            await ctx.guild.ban(user=member, delete_message_days=self.days[delete_messages] if delete_messages else 0,
                                reason=f"{reason} | {ctx.user.display_name}#{ctx.user.discriminator}")
        self.bot.db.insert.bans(guild_id=ctx.guild_id, user_id=member.id, mod_id=ctx.user.id, reason=reason,
                                ts=datetime.now().timestamp())
        embed = Embed(title=f"✅ | {member.display_name}#{member.discriminator} ({member.id}) has been banned")
        await ctx.response.send_message(embed=embed)

    @ban.command(name="remove", description="Unban a user from guild")
    @app_commands.describe(id="ID of the user", reason="Reason to unban member")
    @app_commands.checks.has_permissions(ban_members=True)
    @app_commands.checks.bot_has_permissions(ban_members=True)
    async def ban_remove(self, ctx: Interaction, id: str, reason: Optional[str] = "No reason provided"):
        if id.isalpha():
            return await self.bot.send(ctx, embed=Embed(title=f":x: | Please send a proper id", colour=0xff0000))
        try: # Get the member
            member: User = await self.bot.fetch_user(int(id))
        except NotFound:
            return await self.bot.send(ctx, embed=Embed(title=f":x: | User with the id '{id}' does not exist",
                                                        colour=0xff0000))
        try:  # Check if the member is already banned
            await ctx.guild.fetch_ban(member)
        except NotFound:  # Not banned so move on
            return await ctx.response.send_message(
                embed=Embed(title=f":x: | That member is already unbanned", colour=0xff0000))
        await ctx.guild.unban(user=member, reason=reason)
        self.bot.db.delete.bans(guild_id=ctx.guild_id, user_id=member.id)
        await ctx.response.send_message(
            embed=Embed(title=f"✅ | {member.display_name}#{member.discriminator} ({member.id}) has been unbanned"))

    @massban.command(name="add", description="Mass ban users from guild")
    @app_commands.rename(str_members='members')
    @app_commands.describe(str_members="Space separated list of member ids",
                           delete_messages="How much of their recent messages to delete",
                           reason="Reason to ban members")
    # @app_commands.autocomplete(delete_messages=get_days)
    @app_commands.checks.has_permissions(ban_members=True)
    @app_commands.checks.bot_has_permissions(ban_members=True)
    async def massban_add(self, ctx: Interaction, str_members: str, delete_messages: Optional[str],
                          reason: Optional[str] = "No Reason provided"):
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
            self.bot.db.insert.bans(guild_id=ctx.guild_id, user_id=member.id, mod_id=ctx.user.id, reason=reason,
                                    ts=datetime.now().timestamp())
            success.append(f"{member.display_name}#{member.discriminator} ({id})")
        embed = Embed()
        s_users = "\n".join(success)
        b_users = "\n".join(banned_already)
        f_users = "\n".join(failed)
        embed.add_field(name='Succeeded', value=f">>> {s_users}" if s_users != "" else "None", inline=True)
        embed.add_field(name='Banned Already', value=f">>> {b_users}" if b_users != "" else "None", inline=True)
        embed.add_field(name='Failed', value=f">>> {f_users}" if f_users != "" else "None", inline=True)
        await ctx.response.send_message(embed=embed)

    @massban.command(name='remove', description='Mass unban users from a guild')
    @app_commands.rename(str_members='members')
    @app_commands.describe(str_members="Space separated list of member ids", reason="Reason to ban members")
    @app_commands.checks.has_permissions(ban_members=True)
    @app_commands.checks.bot_has_permissions(ban_members=True)
    async def massban_remove(self, ctx: Interaction, str_members: str, reason: Optional[str] = "No reason provided"):
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
            self.bot.db.delete.bans(guild_id=ctx.guild_id, user_id=member.id)
            success.append(f"{member.display_name}#{member.discriminator} ({id})")
        embed = Embed()
        s_users = "\n".join(success)
        b_users = "\n".join(unbanned_already)
        f_users = "\n".join(failed)
        embed.add_field(name='Succeeded', value=f">>> {s_users}" if s_users != "" else "None", inline=True)
        embed.add_field(name='Banned Already', value=f">>> {b_users}" if b_users != "" else "None", inline=True)
        embed.add_field(name='Failed', value=f">>> {f_users}" if f_users != "" else "None", inline=True)
        await ctx.response.send_message(embed=embed)

    @app_commands.command(name="kick", description="Kick a user from guild")
    @app_commands.describe(member="Member to kick", reason="Why are you kicking this member")
    @app_commands.checks.has_permissions(kick_members=True)
    @app_commands.checks.bot_has_permissions(kick_members=True)
    async def kick(self, ctx: Interaction, member: discord.Member, reason: Optional[str] = "No reason provided"):
        if member.top_role.position < ctx.user.top_role.position or not ctx.guild.owner == ctx.user:
            return await ctx.response.send_message(
                embed=Embed(title=":x: | You need a role higher then the user you are trying to kick",
                            colour=0xff0000))
        elif member == ctx.guild.owner:
            return await ctx.response.send_message(
                embed=Embed(title=":x: | You can not kick the owner of the server",
                            colour=0xff0000))
        elif member == self.bot.user:
            return await ctx.response.send_message(
                embed=Embed(title=":x: | I can not kick myself", colour=0xff0000))

        await member.kick(reason=f"{reason} | {ctx.user.display_name}#{ctx.user.discriminator}")
        embed = Embed(title=f"✅ | {member.display_name}#{member.discriminator} ({member.id}) has been kicked")
        embed.set_author(name=ctx.user)
        await ctx.response.send_message(embed=embed)

    @app_commands.command(name='masskick', description='Mass kick users from a guild')
    @app_commands.describe(members="Space seaparated list of member ids", reason="Why are you kicking these members")
    @app_commands.checks.has_permissions(kick_members=True)
    @app_commands.checks.bot_has_permissions(kick_members=True)
    async def masskick(self, ctx: Interaction, members: str, reason: Optional[str] = "No reason provided"):
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
        await ctx.response.send_message(embed=embed)

    @mute.command(name="add", description="Mute a user in the guild")
    @app_commands.describe(member='Member to mute', minutes='Minutes to mute',
                           reason='Reason to mute member')  # moderate_members
    @app_commands.checks.has_permissions(moderate_members=True)
    @app_commands.checks.bot_has_permissions(moderate_members=True)
    async def mute_add(self, ctx: Interaction, member: discord.Member, minutes: app_commands.Range[float, .1],
                       reason: Optional[str] = "No reason provided"):

        # Check if the member is a member
        # Check if the members role position is lower than your role position
        # Check if the member isn't the owner
        if isinstance(member,
                      Member) and member.top_role.position < ctx.user.top_role.position or not ctx.guild.owner == ctx.user:
            return await ctx.response.send_message(
                embed=Embed(title=":x: | You need a role higher then the user you are trying to mute",
                            colour=0xff0000))

        # Check if the targeted member is the guild owner
        elif member == ctx.guild.owner:
            return await ctx.response.send_message(
                embed=Embed(title=":x: | You can not mute the owner of the server",
                            colour=0xff0000))

        # Check if the targeted member is the current bot
        elif member == self.bot.user:
            return await ctx.response.send_message(
                embed=Embed(title=":x: | I can not mute myself", colour=0xff0000))

        # Member is a part of the guild
        if isinstance(member, Member):
            await member.timeout(datetime.now() + timedelta(minutes=minutes),
                                 reason=f"{reason} | {ctx.user.display_name}#{ctx.user.discriminator}")

        # Member is not a part of the guild
        elif isinstance(member, User):
            return await ctx.response.send_message(Embed(title=':x: | I can not mute a member not in the server',
                                                         colour=0xff0000))
        embed = Embed(title=f"✅ | {member.display_name}#{member.discriminator} ({member.id}) has been muted")
        await ctx.response.send_message(embed=embed)

    @mute.command(name="remove", description="unmute a user from guild")
    @app_commands.describe(member="Member to unmute", reason="Reason to unmute")
    @app_commands.checks.has_permissions(moderate_members=True)
    @app_commands.checks.bot_has_permissions(moderate_members=True)
    async def mute_remove(self, ctx: Interaction, member: discord.Member, reason: Optional[str] = "No reason provided"):
        if not member.timed_out:
            return await ctx.response.send_message(
                embed=Embed(title=f":x: | That member is already unmuted", colour=0xff0000))

        # Member is a part of the guild
        if isinstance(member, Member):
            await member.timeout(datetime.now(), reason=reason)
        # Member is not part of the guild
        elif isinstance(member, User):
            return await ctx.response.send_message(
                embed=Embed(title=f":x: | I can not unmute a member not in the server"))
        await ctx.response.send_message(
            embed=Embed(title=f"✅ | {member.display_name}#{member.discriminator} ({member.id}) has been unmuted"))

    @massmute.command(name="add", description="Mass mute users from guild")
    @app_commands.rename(str_members='members')
    @app_commands.describe(str_members="Space separated list of member ids", minutes="Minutes to mute",
                           reason="Reason to mute members")
    @app_commands.checks.has_permissions(moderate_members=True)
    @app_commands.checks.bot_has_permissions(moderate_members=True)
    async def massmute_add(self, ctx: Interaction, str_members: str, minutes: app_commands.Range[float, .1],
                           reason: Optional[str]):
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
            await member.timeout(datetime.now() + timedelta(minutes=minutes),
                                 reason=f"{reason} | {ctx.user.display_name}#{ctx.user.discriminator}")
            success.append(f"{member.display_name}#{member.discriminator} ({id})")
        embed = Embed()
        s_users = "\n".join(success)
        m_users = "\n".join(muted_already)
        f_users = "\n".join(failed)
        embed.add_field(name='Succeeded', value=f">>> {s_users}" if s_users != "" else "None", inline=True)
        embed.add_field(name='Muted Already', value=f">>> {m_users}" if m_users != "" else "None", inline=True)
        embed.add_field(name='Failed', value=f">>> {f_users}" if f_users != "" else "None", inline=True)
        await ctx.response.send_message(embed=embed)

    @massmute.command(name='remove', description='Mass unmute users from a guild')
    @app_commands.rename(str_members='members')
    @app_commands.describe(str_members="Space separated list of member ids", reason="reason to unmute members")
    @app_commands.checks.has_permissions(moderate_members=True)
    @app_commands.checks.bot_has_permissions(moderate_members=True)
    async def massmute_remove(self, ctx: Interaction, str_members: str, reason: Optional[str] = "No reason provided"):
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

            await member.timeout(datetime.now(),
                                 reason=f"{reason} | {ctx.user.display_name}#{ctx.user.discriminator}")
            success.append(f"{member.display_name}#{member.discriminator} ({id})")
        embed = Embed()
        s_users = "\n".join(success)
        m_users = "\n".join(unmutted_alread)
        f_users = "\n".join(failed)
        embed.add_field(name='Succeeded', value=f">>> {s_users}" if s_users != "" else "None", inline=True)
        embed.add_field(name='Muted Already', value=f">>> {m_users}" if m_users != "" else "None", inline=True)
        embed.add_field(name='Failed', value=f">>> {f_users}" if f_users != "" else "None", inline=True)

    @app_commands.command(name='report', description='Report a user')
    @app_commands.describe(member="Member to report", reason="Reason to report the member")
    async def report(self, ctx: Interaction, member: discord.Member, reason: str):
        pass

    @purge.command(name='all', description='Removes all messages')
    @app_commands.describe(limit="Amount of messages to purge 1-1000. Default 100",
                           reason="Reason for deleting messages")  # manage_messages=True, read_message_history=True
    @app_commands.checks.has_permissions(manage_messages=True, read_message_history=True)
    @app_commands.checks.bot_has_permissions(manage_messages=True, read_message_history=True)
    async def purge_all(self, ctx: Interaction, limit: Optional[app_commands.Range[int, 1, 1000]] = 100,
                        reason: Optional[str] = "No reason provided"):
        await ctx.response.defer()
        messages = await ctx.channel.purge(limit=limit, before=discord.utils.snowflake_time(ctx.id),
                                           reason=reason)
        msg = await ctx.response.send_message(
            embed=Embed(title=f'✅ | Successfully purged {len(messages)} messages'))
        await msg.delete(delay=3)

    @purge.command(name='bot', description='Removes all bot messages')
    @app_commands.describe(limit="Amount of messages to purge 1-1000. Default 100",
                           reason="Reason for deleting messages")
    @app_commands.checks.has_permissions(manage_messages=True, read_message_history=True)
    @app_commands.checks.bot_has_permissions(manage_messages=True, read_message_history=True)
    async def purge_bot(self, ctx: Interaction, limit: Optional[app_commands.Range[int, 1, 1000]] = 100,
                        reason: Optional[str] = "No reason provided"):
        await ctx.response.defer()
        messages = await ctx.channel.purge(limit=limit, before=discord.utils.snowflake_time(ctx.id),
                                           reason=reason, check=lambda message: message.author.bot)
        msg = await ctx.response.send_message(
            embed=Embed(title=f'✅ | Successfully purged {len(messages)} bot messages'))
        await msg.delete(delay=3)

    @purge.command(name='user', description='Purge messages from a channel')
    @app_commands.describe(target="User to target", limit="Amount of messages to purge 1-1000. Default 100",
                           reason="Reason for deleting messages")
    @app_commands.checks.has_permissions(manage_messages=True, read_message_history=True)
    @app_commands.checks.bot_has_permissions(manage_messages=True, read_message_history=True)
    async def purge_user(self, ctx: Interaction, target: discord.Member,
                         limit: Optional[app_commands.Range[int, 1, 1000]] = 100,
                         reason: Optional[str] = "No reason provided"):
        await ctx.response.defer()
        messages = await ctx.channel.purge(limit=limit, before=discord.utils.snowflake_time(ctx.id),
                                           reason=reason, check=lambda message: message.user.id == target.id)
        msg = await ctx.response.send_message(
            embed=Embed(
                title=f'✅ | Successfully purged {len(messages)} messages fro {target.display_name}#{target.discriminator}'))
        await msg.delete(delay=3)

    @purge.command(name='contains', description='Removes all messages containing a string')
    @app_commands.describe(string='String to target', limit="Amount of messages to purge 1-1000. Default 100")
    @app_commands.checks.has_permissions(manage_messages=True, read_message_history=True)
    @app_commands.checks.bot_has_permissions(manage_messages=True, read_message_history=True)
    async def purge_contains(self, ctx: Interaction, string: str,
                             limit: Optional[app_commands.Range[int, 1, 1000]] = 100,
                             reason: Optional[str] = "No reason provided"):
        await ctx.response.defer()
        messages = await ctx.channel.purge(limit=limit, before=discord.utils.snowflake_time(ctx.id),
                                           reason=reason,
                                           check=lambda message: string.lower() in message.content.lower())
        msg = await ctx.response.send_message(
            embed=Embed(title=f'✅ | Successfully purged {len(messages)} messages containing {string}'))
        await msg.delete(delay=3)

    @purge.command(name='human', description='Removes all non-bot messages')
    @app_commands.describe(limit="Amount of messages to purge 1-1000. Default 100",
                           reason="Reason for deleting messages")
    @app_commands.checks.has_permissions(manage_messages=True, read_message_history=True)
    @app_commands.checks.bot_has_permissions(manage_messages=True, read_message_history=True)
    async def purge_human(self, ctx: Interaction, limit: Optional[app_commands.Range[int, 1, 1000]] = 100,
                          reason: Optional[str] = "No reason provided"):
        await ctx.response.defer()
        messages = await ctx.channel.purge(limit=limit, before=discord.utils.snowflake_time(ctx.id),
                                           reason=reason,
                                           check=lambda message: not message.author.bot)
        msg = await ctx.response.send_message(
            embed=Embed(title=f'✅ | Successfully purged {len(messages)} human messages'))
        await msg.delete(delay=3)


async def setup(bot):
    await bot.add_cog(Mod(bot))
