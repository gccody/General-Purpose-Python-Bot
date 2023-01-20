import asyncio
import atexit
import glob
import sys

from time import sleep

import numpy as np
import requests

from lib.bot import Bot
from lib.config import Config
from lib.progress import Progress
from asyncer import asyncify

COGS = [path.split("\\")[-1][:-3] if "\\" in path else path.split("/")[-1][:-3] for path in
        glob.glob('./lib/cogs/*.py')]
VERSION = "0.0.1"
config = Config()
TOTAL_GUILDS = len(requests.get("https://discord.com/api/v9/users/@me/guilds",
                                headers={"Authorization": f"Bot {config.token}"}).json())
SHARDS_LIST: list[int] = list(range(round((TOTAL_GUILDS / 1000) + 1)))
CLUSTERS = round((len(SHARDS_LIST) / 2) + 1)
SHARDS_SPLIT: list[np.ndarray[int]] = np.array_split(SHARDS_LIST, CLUSTERS)


def start(cluster_id: int):
    bot: Bot = Bot(list((SHARDS_SPLIT[cluster_id])), VERSION)
    progress = Progress("Registering Cogs", len(COGS))
    for index, cog in enumerate(COGS):
        bot.load_extension(f"lib.cogs.{cog}")
        # sleep(.2)
        progress.next()
    atexit.register(bot.db.commit)
    bot.run(bot.config.token)


if __name__ == '__main__':
    start(0)
