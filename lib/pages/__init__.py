import random
from datetime import datetime
from typing import Union, Optional

import discord
from discord.ext import pages
from discord.ext.bridge import BridgeContext
from discord.embeds import Embed


class Pagination(pages.Paginator):
    logo_path = "https://i.imgur.com/QMykWjw.png"

    async def respond(
        self,
        interaction: Union[discord.Interaction, BridgeContext],
        ephemeral: bool = False,
        target: Optional[discord.abc.Messageable] = None,
        target_message: str = "Paginator sent!",
    ) -> Union[discord.Message, discord.WebhookMessage]:
        for page in self.pages:
            if isinstance(page, Embed):
                if not isinstance(page.colour, discord.Colour):
                    color = int("0x" + ''.join([random.choice('0123456789ABCDEF') for j in range(6)]), 16)
                    page.colour = color
                page.set_footer(text="Made by Gccody")
                page.timestamp = datetime.now()
                continue

            for embed in page.embeds:
                if not isinstance(embed.colour, discord.Colour):
                    color = int("0x" + ''.join([random.choice('0123456789ABCDEF') for j in range(6)]), 16)
                    embed.colour = color
                embed.set_footer(text="Made by Gccody")
                embed.timestamp = datetime.now()

        return await super().respond(interaction, ephemeral, target, target_message)
