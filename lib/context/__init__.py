from datetime import datetime
import random

import discord
from discord import ApplicationContext, Interaction, WebhookMessage
from discord.embeds import Embed


class CustomContext(ApplicationContext):
    logo_path = "https://i.imgur.com/QMykWjw.png"

    async def respond(self, *args, **kwargs) -> Interaction | WebhookMessage:
        if kwargs.get('embed'):
            embed: Embed = kwargs['embed']
            if not isinstance(embed.colour, discord.Colour):
                color = int("0x"+''.join([random.choice('0123456789ABCDEF') for j in range(6)]), 16)
                embed.colour = color
            embed.set_footer(text="Made by Gccody")
            embed.timestamp = datetime.now()
            # embed.set_thumbnail(url=self.logo_path)
            kwargs['embed'] = embed
            return await super().respond(*args, **kwargs)
        else:
            return await super().respond(*args, **kwargs)