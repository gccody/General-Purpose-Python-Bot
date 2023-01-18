import random

import discord
from discord.ext.commands import Cog
from discord.commands import option,slash_command
from discord.commands import SlashCommandGroup
from discord.embeds import Embed

from lib.bot import Bot
from lib.context import CustomContext
from lib.pages import Pagination

from expiringdict import ExpiringDict


class Fun(Cog):
    def __init__(self, bot: Bot):
        self.bot: Bot = bot
        self.cache = ExpiringDict(max_len=100, max_age_seconds=3600)

    urban = SlashCommandGroup('urban')

    @slash_command(name='eightball', description='Make predictions')
    @option('question',
            str,
            description='Yes/No question',
            required=True)
    async def eightball(self, ctx: CustomContext, question: str):
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
        await ctx.respond(embed=Embed(title=f':8ball: | {random.choice(responses)}, {ctx.user.display_name}'))

    @slash_command(name='embed')
    @option('title',
            str,
            description='Title of embed',
            required=False)
    @option('title_url',
            str,
            description='Url embeded into title',
            required=False)
    @option('author',
            discord.Member,
            description='Author of the embed')
    async def embed_message(self, ctx: CustomContext):
        pass

    @urban.command(name='define', description='Define a word in the urban dictionary')
    @option('word',
            str,
            description='Word to look up',
            required=True)
    async def urban_define(self, ctx: CustomContext, word: str):
        res = self.bot.urban.define_word(word)
        if not res:
            return await ctx.respond(embed=Embed(title=f':x: | Failed to find word: {word}', colour=0xff0000))
        embeds: list[Embed] = []
        for definition in res:
            embeds.append(Embed(title=word.title(), description=definition))
        paginator = Pagination(pages=embeds)
        await paginator.respond(ctx.interaction)




def setup(bot):
    bot.add_cog(Fun(bot))
