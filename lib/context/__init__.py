from datetime import datetime
from discord import ApplicationContext, Interaction, WebhookMessage
from discord.embeds import Embed


class CustomContext(ApplicationContext):
    logo_path = "https://i.imgur.com/QMykWjw.png"

    async def respond(self, *args, **kwargs) -> Interaction | WebhookMessage:
        if kwargs.get('embed'):
            embed: Embed = kwargs['embed']
            embed.set_footer(text="Made by Gccody", icon_url=self.logo_path)
            embed.timestamp = datetime.now()
            embed.set_thumbnail(url=self.logo_path)
            kwargs['embed'] = embed
            return await super().respond(*args, **kwargs)
        else:
            return await super().respond(*args, **kwargs)