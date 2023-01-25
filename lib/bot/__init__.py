import asyncio
import json
import os
import random
from datetime import datetime
from typing import Any

import discord
import psutil
import tzlocal
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from discord import Guild, Interaction, VoiceChannel
from discord.app_commands import Command
from discord.embeds import Embed
from discord.errors import NotFound, InteractionResponded
from discord.ext.commands import AutoShardedBot
from discord.ext.commands.errors import CommandNotFound, BadArgument

from lib.cache import Cache
from lib.config import Config
from lib.db import DB
from lib.progress import Progress, Timer, Loading
from lib.urban import UrbanDictionary

COMMAND_ERROR_REGEX = r"Command raised an exception: (.*?(?=: )): (.*)"
IGNORE_EXCEPTIONS = (CommandNotFound, BadArgument, RuntimeError)


def synchronize_async_helper(to_await):
    async_response = []

    async def run_and_capture_result():
        r = await to_await
        async_response.append(r)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(run_and_capture_result())
    return async_response[0]


class Bot(AutoShardedBot):
    def __init__(self, shards: list[int], version: str):
        self.config: Config = Config()
        self.db: DB = DB()
        self.cache: Cache = Cache()
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
            description="Misc Bot used for advanced moderation and guild customization",)
        self.tasks.add_job(self.db.commit, trigger='interval', minutes=30)
        self.shard_progress.start()

    async def on_connect(self):
        while not self.shards_ready:
            await asyncio.sleep(.5)
        loading: Loading = Loading("Syncing commands")
        asyncio.ensure_future(loading.start())
        self.tree.copy_global_to(guild=discord.Object(id="1064582321728143421"))
        commands = await self.tree.sync(guild=discord.Object(id="1064582321728143421"))
        loading.stop(f"Synced {len(commands)} commands")
        await self.register_guilds()
        # asyncio.ensure_future(self.monitor_shutdown())
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
            self.db.insert.commands(command_name=name, guild_id=ctx.guild_id, user_id=ctx.user.id,
                                    params=json.dumps(options), ts=datetime.now().timestamp())
            await self.db.run(f"""INSERT INTO commands VALUES (?,?,?,?,?)""", name, ctx.guild_id,
                              ctx.user.id, json.dumps(options), datetime.now().timestamp())

    @staticmethod
    async def send(ctx: Interaction, *args, **kwargs):
        if kwargs.get('embed'):
            embed: Embed = kwargs['embed']
            if embed.colour is None:
                color = int("0x" + ''.join([random.choice('0123456789ABCDEF') for j in range(6)]), 16)
                embed.colour = color
            embed.set_footer(text="Made by Gccody")
            embed.timestamp = datetime.now()
            kwargs['embed'] = embed

        if ctx.is_expired():
            channel = ctx.channel
            if not isinstance(channel, VoiceChannel):
                return await ctx.channel.send(*args, **kwargs)
        try:
            return await ctx.response.send_message(*args, **kwargs)
        except InteractionResponded:
            try:
                return await ctx.followup.send(*args, **kwargs)
            except NotFound:
                return await ctx.channel.send(*args, **kwargs)

    async def monitor_shutdown(self):
        while True:
            if psutil.Process().status() == psutil.STATUS_ZOMBIE:
                await self.db.commit()
                await self.close()
                raise SystemExit
            if psutil.process_iter(['pid', 'name']):
                for process in psutil.process_iter():
                    if process.name() == 'shutdown.exe':
                        await self.db.commit()
                        await self.close()
                        raise SystemExit
            await asyncio.sleep(1)

    async def register_guilds(self):
        progress = Progress('Registering guilds', len(self.guilds))
        progress.start()
        for guild in self.guilds:
            await self.db.insert.guilds(id=guild.id)
            progress.next()

        for guild in (await self.db.get.guilds()):
            if not self.get_guild(guild.id):
                await self.db.delete.guilds(id=guild.id)
        await self.db.commit()
        self.ready = True
        self.tasks.start()

    async def on_guild_join(self, guild: Guild):
        self.db.insert.guilds(id=guild.id)

    async def on_guild_remove(self, guild: Guild):
        self.db.delete.guilds(id=guild.id)

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
