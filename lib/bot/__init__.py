import asyncio
import json
import os
from datetime import datetime
import random
from typing import Any

import discord
import psutil
import tzlocal
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from discord import Guild, Interaction, VoiceChannel
from discord.app_commands import Command
from discord.embeds import Embed
from discord.errors import NotFound
from discord.ext.commands import AutoShardedBot
from discord.ext.commands.errors import CommandNotFound, BadArgument

from lib.config import Config
from lib.db import DB
from lib.progress import Progress, Timer
from lib.urban import UrbanDictionary

COMMAND_ERROR_REGEX = r"Command raised an exception: (.*?(?=: )): (.*)"
IGNORE_EXCEPTIONS = (CommandNotFound, BadArgument, RuntimeError)


class Bot(AutoShardedBot):
    def __init__(self, shards: list[int], version: str):
        self.config: Config = Config()
        self.db: DB = DB()
        self.db.build()
        self.cache: dict = dict()
        self.tasks = AsyncIOScheduler(timezone=str(tzlocal.get_localzone()))
        self.shards_ready = False
        self.ready = False
        self.expected_shards = len(shards)
        self.timer = Timer()
        self.shard_progress = Progress('Shards Ready', self.expected_shards)
        self.urban: UrbanDictionary = UrbanDictionary()
        self.VERSION = version
        super().__init__(
            command_prefix=None,
            owner_id="507214515641778187",
            shards=shards,
            intents=discord.Intents.all(),
            description="Misc Bot used for advanced moderation and guild customization")
        self.tasks.add_job(self.db.commit, trigger='interval', minutes=30)
        self.shard_progress.start()

    async def on_connect(self):
        await self.tree.sync()
        while not self.shards_ready:
            print('Shards Not Ready')
            await asyncio.sleep(.5)
        self.register_guilds()
        print(f"Signed into {self.user.display_name}#{self.user.discriminator}")
        # asyncio.ensure_future(self.timer.start())

    async def on_shard_ready(self, shard_id):
        await self.change_presence(activity=discord.Activity(type=discord.ActivityType.watching,
                                                             name=f"SHARD {shard_id}"),
                                   shard_id=shard_id)
        self.shard_progress.next()
        if shard_id + 1 == self.expected_shards:
            self.shards_ready = True

    async def on_interaction(self, ctx: Interaction):
        if isinstance(ctx.command, Command):
            name_list, options = self.get_name(ctx.data, [])
            name = " ".join(name_list)
            self.db.run(f"""INSERT INTO commands VALUES (?,?,?,?,?)""", name, ctx.guild_id,
                            ctx.user.id, json.dumps(options), datetime.now().timestamp())

    @staticmethod
    async def send(ctx: Interaction, *args, **kwargs):
        if kwargs.get('embed'):
            embed: Embed = kwargs['embed']
            if not isinstance(embed.colour, discord.Colour):
                color = int("0x" + ''.join([random.choice('0123456789ABCDEF') for j in range(6)]), 16)
                embed.colour = color
            embed.set_footer(text="Made by Gccody")
            embed.timestamp = datetime.now()
            # embed.set_thumbnail(url=self.logo_path)
            kwargs['embed'] = embed
        if ctx.is_expired():
            channel = ctx.channel
            if not isinstance(channel, VoiceChannel):
                return await ctx.channel.send(*args, **kwargs)
        try:
            await ctx.original_response()
            return await ctx.followup.send(*args, **kwargs)
        except NotFound:
            return await ctx.response.send_message(*args, **kwargs)

    def register_guilds(self):
        progress = Progress('Registering guilds', len(self.guilds))
        for guild in self.guilds:
            self.db.run("""INSERT OR IGNORE INTO guilds VALUES (?,?,?)""", guild.id, None, None)
            progress.next()

        for guild in self.db.get.guilds():
            if not self.get_guild(guild.id):
                self.db.run("""DELETE FROM guilds WHERE id=?""", guild.id)
        self.db.commit()
        self.ready = True
        print('End')
        self.tasks.start()

    async def on_guild_join(self, guild: Guild):
        self.db.run("""INSERT OR IGNORE INTO guilds VALUES (?,?,?)""", guild.id, None, None)

    async def on_guild_remove(self, guild: Guild):
        self.db.run("""DELETE FROM guilds WHERE id=?""", guild.id)

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

    @staticmethod
    async def cpu_percent(interval=None, *args, **kwargs):
        python_process = psutil.Process(os.getpid())
        if interval is not None and interval > 0.0:
            python_process.cpu_percent(*args, **kwargs)
            await asyncio.sleep(interval)
        return psutil.cpu_percent(*args, **kwargs)
