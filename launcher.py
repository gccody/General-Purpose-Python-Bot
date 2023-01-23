import asyncio
import atexit
import glob
from http.client import HTTPException

import discord
import numpy as np
import requests
from discord import Embed, NotFound, Interaction
from discord.app_commands import CommandOnCooldown, MissingPermissions, BotMissingPermissions

from lib.bot import Bot, IGNORE_EXCEPTIONS
from lib.config import Config
from lib.progress import Progress

COGS = [path.split("\\")[-1][:-3] if "\\" in path else path.split("/")[-1][:-3] for path in
        glob.glob('./lib/cogs/*.py')]
VERSION = "0.0.1"
config = Config()
TOTAL_GUILDS = len(requests.get("https://discord.com/api/v9/users/@me/guilds",
                                headers={"Authorization": f"Bot {config.token}"}).json())
SHARDS_LIST: list[int] = list(range(round((TOTAL_GUILDS / 1000) + 1)))
CLUSTERS = round((len(SHARDS_LIST) / 2) + 1)
SHARDS_SPLIT: list[np.ndarray[int]] = np.array_split(SHARDS_LIST, CLUSTERS)


async def start():
    bot = Bot(SHARDS_LIST, VERSION)
    progress = Progress("Registering Cogs", len(COGS))
    for index, cog in enumerate(COGS):
        await bot.load_extension(f"lib.cogs.{cog}")
        progress.next()

        # @bot.event
        # async def on_interaction(ctx: Interaction):
        #     if isinstance(ctx.command, Command):
        #         print('is Command')
        #         raise BotNotReady()

        @bot.tree.error
        async def on_command_error(ctx: Interaction, exc) -> None:
            if any([isinstance(exc, error) for error in IGNORE_EXCEPTIONS]):
                pass
            elif isinstance(exc, CommandOnCooldown):
                embed: Embed = Embed(title='Command on Cooldown',
                                     description=f"That command is on cooldown. Try again in {exc.retry_after:,.2f} seconds.",
                                     colour=0xff0000)
                await bot.send(ctx, embed=embed)
            elif isinstance(exc, MissingPermissions):
                embed: Embed = Embed(title='You are missing permissions', description=f'>>> {exc}', colour=0xff0000)
                await bot.send(ctx, embed=embed)
            elif isinstance(exc, BotMissingPermissions):
                embed: Embed = Embed(title='Bot Missing Permissions', description=f">>> {exc}", colour=0xff0000)
                await bot.send(ctx, embed=embed)
            elif isinstance(exc, HTTPException):
                embed: Embed = Embed(title="Http Error", description='Message failed to send', colour=0xff0000)
                await bot.send(ctx, embed=embed)
            elif isinstance(exc, NotFound):
                await bot.send(ctx,
                    embed=Embed(title='Not Found Error', description='One or more items could not be found.',
                                colour=0xff0000))
            elif hasattr(exc, "original"):
                if isinstance(exc.original, HTTPException):
                    embed: Embed = Embed(title="Http Error", description='Message failed to send', colour=0xff0000)
                    await bot.send(ctx, embed=embed)
                if isinstance(exc.original, discord.Forbidden):
                    embed: Embed = Embed(title='Forbidden Error', description='Insufficient Permissions',
                                         colour=0xff0000)
                    await bot.send(ctx, embed=embed)
                else:
                    raise exc.original

            else:
                raise exc

    async def exit_handler():
        bot.db.commit()
        await bot.close()

    atexit.register(exit_handler)
    await bot.start(bot.config.token)


if __name__ == '__main__':
    asyncio.run(start())
