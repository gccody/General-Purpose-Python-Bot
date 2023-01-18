import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import tzlocal

from datetime import datetime
import json
from typing import Any

import discord
from discord.ext.commands import AutoShardedBot as BaseBot
from discord.ext.commands.errors import CommandNotFound, BadArgument, MissingRequiredArgument, CommandOnCooldown, \
    MissingPermissions, BotMissingPermissions
from discord.errors import NotFound
from http.client import HTTPException
from discord.embeds import Embed
from lib.config import Config
from lib.db import DB
from discord import Interaction, Guild
from lib.context import CustomContext
from lib.urban import UrbanDictionary

COMMAND_ERROR_REGEX = r"Command raised an exception: (.*?(?=: )): (.*)"
IGNORE_EXCEPTIONS = (CommandNotFound, BadArgument, RuntimeError)


class Bot(BaseBot):
    def __init__(self, version: str):
        self.config: Config = Config()

        self.db: DB = DB()
        self.db.build()
        self.cache: dict = dict()
        self.tasks = AsyncIOScheduler(timezone=str(tzlocal.get_localzone()))
        self.urban: UrbanDictionary = UrbanDictionary()
        self.VERSION = version
        super().__init__(
                         owner_id="507214515641778187",
                         shards=5000,
                         intents=discord.Intents.all(),
                         description="Misc Bot used for advanced moderation and guild customization")
        self.tasks.add_job(self.db.commit, trigger='interval', minutes=30)

    async def on_connect(self):
        self.tasks.start()
        await self.sync_commands()
        print(f"Signed into {self.user.display_name}#{self.user.discriminator}\n")

    async def on_shard_ready(self, shard_id):
        await self.change_presence(activity=discord.Activity(type=discord.ActivityType.watching,
                                                             name=f"SHARD {shard_id}"),
                                   shard_id=shard_id)
        print(f" - Shard {shard_id+1}/{self.shard_count} ready")

    async def get_application_context(
        self, interaction: Interaction, cls=CustomContext
    ):
        return await super().get_application_context(interaction, cls=cls)

    async def on_disconnect(self):
        print(f"Bot Disconnected, Retrying to sign into user {self.user.display_name}#{self.user.discriminator}")

    async def on_guild_join(self, guild: Guild):
        self.db.execute("""INSERT OR IGNORE INTO guilds VALUES (?,?,?)""", guild.id, None, None)

    async def on_guild_remove(self, guild: Guild):
        self.db.execute("""DELETE FROM guilds WHERE id=?""", guild.id)

    def get_name(self, data: Any, groups: list[str]):
        if isinstance(data, dict):
            if not data.get('options'):
                return [*groups, data.get('name')], []
            else:
                for option in data.get('options'):
                    if option.get('type') not in [1, 2]:
                        return [*groups, data.get('name')], data.get('options')
                else:
                    return self.get_name(data.get('options'), [*groups, data.get('name')])
        else:
            data = data[0]
            if not data.get('options'):
                return [*groups, data.get('name')], []
            else:
                for option in data.get('options'):
                    if option.get('type') not in [1, 2]:
                        return [*groups, data.get('name')], data.get('options')
                else:
                    return self.get_name(data.get('options'), [*groups, data.get('name')])

    async def on_interaction(self, interaction: discord.Interaction):
        if interaction.is_command():
            name_list, options = self.get_name(interaction.data, [])
            name = " ".join(name_list)
            # self.db.execute(f"""INSERT INTO commands VALUES (?,?,?,?,?)""", name, interaction.guild_id, interaction.user.id, json.dumps(options), datetime.now().timestamp())
        return await super().on_interaction(interaction=interaction)

    async def on_application_command_error(self, ctx: CustomContext, exc) -> None:
        if any([isinstance(exc, error) for error in IGNORE_EXCEPTIONS]):
            pass
        elif isinstance(exc, MissingRequiredArgument):
            await ctx.respond("One or more required arguments are missing.")
        elif isinstance(exc, CommandOnCooldown):
            embed: Embed = Embed(title='Command on Cooldown',
                                 description=f"That command is on cooldown. Try again in {exc.retry_after:,.2f} seconds.",
                                 colour=0xff0000)
            await ctx.respond(embed=embed)
        elif isinstance(exc, MissingPermissions):
            embed: Embed = Embed(title='You are missing permissions', description=f'>>> {exc}', colour=0xff0000)
        elif isinstance(exc, BotMissingPermissions):
            embed: Embed = Embed(title='Bot Missing Permissions', description=f">>> {exc}", colour=0xff0000)
            await ctx.respond(embed=embed)
        elif isinstance(exc, HTTPException):
            embed: Embed = Embed(title="Http Error", description='Message failed to send', colour=0xff0000)
            await ctx.respond(embed=embed)
        elif isinstance(exc, NotFound):
            await ctx.respond(embed=Embed(title='Not Found Error', description='One or more items could not be found.', colour=0xff0000))
        elif hasattr(exc, "original"):
            if isinstance(exc.original, HTTPException):
                embed: Embed = Embed(title="Http Error", description='Message failed to send', colour=0xff0000)
                await ctx.respond(embed=embed)
            if isinstance(exc.original, discord.Forbidden):
                await ctx.message.delete()
                embed: Embed = Embed(title='Forbidden Error', description='Insufficient Permissions', colour=0xff0000)
                await ctx.respond(embed=embed)
            else:
                raise exc.original

        else:
            raise exc
