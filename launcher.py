import glob
from lib.bot import Bot
from lib.context import CustomContext

COGS = [path.split("\\")[-1][:-3] if "\\" in path else path.split("/")[-1][:-3] for path in
        glob.glob('./lib/cogs/*.py')]
VERSION = "0.5.0"
bot: Bot = Bot(VERSION)
print("Registering cogs...")
for cog in COGS:
    print(f" - {cog}")
    bot.load_extension(f"lib.cogs.{cog}")
print("All cogs ready, now registering shards...")


@bot.slash_command()
async def ping(ctx: CustomContext):
    await ctx.send("Pong!")


if __name__ == '__main__':
    bot.run(bot.config.token)
