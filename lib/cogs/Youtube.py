import re

from discord.ext.commands import Cog
from discord.commands import slash_command, SlashCommandGroup, option
from discord.embeds import Embed
import aiohttp

from bs4 import BeautifulSoup

from lib.bot import Bot
from lib.context import CustomContext


class Youtube(Cog):
    def __init__(self, bot):
        self.bot: Bot = bot

    youtube = SlashCommandGroup('youtube')

    async def check_channel(self, handle: str, message: str, guild_id: str):
        async with aiohttp.ClientSession() as session:
            res = await session.get(f"https://youtube.com/@{handle}/videos")
            html = await res.text()
            try:
                latest_video_url = "https://www.youtube.com/watch?v=" + re.search('(?<="videoId":").*?(?=")',
                                                                                  html).group()
            except AttributeError:
                latest_video_url = ""

    @youtube.command(name='notify', description='Get a ping when this user uploads')
    @option('handle',
            str,
            description='Youtube handle',
            required=True)
    @option('message',
            str,
            description='Message to send when video is uploaded',
            required=False)
    @option('channel',
            str,
            description='Channel to send announcement',
            required=False)
    async def youtube_notify(self, ctx: CustomContext, handle: str, message: str | None):
        async with aiohttp.ClientSession() as session:
            res = await session.get(f"https://youtube.com/@{handle}/videos")
            if res.status == 404:
                return await ctx.respond(embed=Embed(title=':x: | Channel not found', colour=0xff0000))
            elif res.status not in range(200, 300):
                return await ctx.respond(embed=Embed(title=':x: | Something went wrong', colour=0xff0000))

            user = self.bot.db.record("""SELECT * FROM youtube WHERE handle = ? AND guild_id = ?""", handle,
                                      ctx.guild_id)
            if user:
                return await ctx.respond(embed=Embed(title=':x: | Already watching for new videos', colour=0xff0000))

            res = await session.get(f"https://youtube.com/@{handle}/videos")
            html = await res.text()

        try:
            latest_video_url = "https://www.youtube.com/watch?v=" + re.search('(?<="videoId":").*?(?=")', html).group()
        except AttributeError:
            latest_video_url = ""
        self.bot.db.execute("""INSERT INTO youtube VALUES (?,?,?,?)""", handle, ctx.guild_id,
                            message if message else f"@{handle} has uploaded a video", latest_video_url)
        await ctx.respond(embed=Embed(title=f'✅ | Waiting for @{handle} to post more videos'))
        self.bot.tasks.add_job(id=f"{handle}|{ctx.guild_id}", args=(handle, message, ctx.guild_id,), trigger='interval',
                               minutes=1)


def setup(bot):
    bot.add_cog(Youtube(bot))
