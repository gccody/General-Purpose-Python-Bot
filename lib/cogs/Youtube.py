import re
from typing import Optional

from discord.ext.commands import Cog
from discord.channel import TextChannel
from discord import app_commands, Interaction
from discord.embeds import Embed
import aiohttp

from lib.bot import Bot


class Youtube(Cog):
    youtube = app_commands.Group(name='youtube', description='Search youtube')

    def __init__(self, bot):
        self.bot: Bot = bot

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
    @app_commands.describe(handle='Youtube handle', message='Message to send when video is uploaded', channel='Channel to send announcement')
    async def youtube_notify(self, ctx: Interaction, handle: str, message: Optional[str], channel: Optional[TextChannel]):
        async with aiohttp.ClientSession() as session:
            res = await session.get(f"https://youtube.com/@{handle}/videos")
            if res.status == 404:
                return await ctx.response.send_message(embed=Embed(title=':x: | Channel not found', colour=0xff0000))
            elif res.status not in range(200, 300):
                return await ctx.response.send_message(embed=Embed(title=':x: | Something went wrong', colour=0xff0000))

            user = self.bot.db.get.youtube(handle=handle, guild_id=ctx.guild_id)
            if user:
                return await ctx.response.send_message(embed=Embed(title=':x: | Already watching for new videos', colour=0xff0000))

            res = await session.get(f"https://youtube.com/@{handle}/videos")
            html = await res.text()

        try:
            latest_video_url = "https://www.youtube.com/watch?v=" + re.search('(?<="videoId":").*?(?=")', html).group()
        except AttributeError:
            latest_video_url = ""
        self.bot.db.insert.youtube(handle=handle, guild_id=ctx.guild_id, message=message if message else f"@{handle} has uploaded a video", latest_url=latest_video_url)
        await ctx.response.send_message(embed=Embed(title=f'✅ | Waiting for @{handle} to post more videos'))
        self.bot.tasks.add_job(id=f"{handle}|{ctx.guild_id}", args=(handle, message, ctx.guild_id,), trigger='interval',
                               minutes=1)


async def setup(bot):
    await bot.add_cog(Youtube(bot))
