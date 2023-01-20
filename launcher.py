import glob
import atexit
from lib.bot import Bot

COGS = [path.split("\\")[-1][:-3] if "\\" in path else path.split("/")[-1][:-3] for path in
        glob.glob('./lib/cogs/*.py')]
VERSION = "0.0.1"
bot: Bot = Bot(VERSION)
print("Registering cogs...")
for cog in COGS:
    print(f" - {cog}")
    bot.load_extension(f"lib.cogs.{cog}")
print("All cogs ready, now registering shards...")


if __name__ == '__main__':
    atexit.register(bot.db.commit)
    bot.run(bot.config.token)
