import random
from typing import Optional

import discord
from discord.ext.commands import Cog
from discord import app_commands, Interaction
from discord.embeds import Embed

from lib.bot import Bot

from expiringdict import ExpiringDict

from lib.pages import Pagination


class Fun(Cog):
    urban = app_commands.Group(name='urban', description='Search the urban dictionary')

    def __init__(self, bot: Bot):
        self.bot: Bot = bot
        self.cache = ExpiringDict(max_len=100, max_age_seconds=3600)

    @app_commands.command(name='eightball', description='Make predictions')
    @app_commands.describe(question='Yes/No question')
    async def eightball(self, ctx: Interaction, question: str):
        responses = [
            'It is certain',
            'Reply hazy, try again',
            'Don\'t count on it',
            'It is decidedly so',
            'Ask again later',
            'My reply is no',
            'Without a doubt',
            'Better not tell you now',
            'My sources say no',
            'Yes definitely',
            'Cannot predict now',
            'Outlook not so good',
            'You may rely on it',
            'Concentrate and ask again',
            'Very doubtful',
            'As I see it, yes',
            'Most likely',
            'Outlook good',
            'Yes',
            'No',
            'Signs point to yes',
            'Signs point to no',
            'Most likely not',
        ]
        await self.bot.send(ctx, embed=Embed(title=f':8ball: | {random.choice(responses)}, {ctx.user.display_name}'))

    @app_commands.command(name='embed')
    @app_commands.describe(title='Title of embed', title_url='Url embeded into title', author='Author of the embed')
    async def embed_message(self, ctx: Interaction, title: Optional[str], title_url: Optional[str], author: Optional[discord.Member]):
        pass

    @urban.command(name='define', description='Define a word in the urban dictionary')
    @app_commands.describe(word='Word to look up')
    async def urban_define(self, ctx: Interaction, word: str):
        await ctx.response.defer()
        res = self.bot.urban.define_word(word)
        if not res:
            return await ctx.response.send_message(embed=Embed(title=f':x: | Failed to find word: {word}', colour=0xff0000))
        embeds: list[Embed] = []
        for definition in res:
            embeds.append(Embed(title=word.title(), description=definition))
        paginator = Pagination(bot=self.bot)
        await paginator.start(ctx, pages=embeds)


async def setup(bot):
    await bot.add_cog(Fun(bot))
