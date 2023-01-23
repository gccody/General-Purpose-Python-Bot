from discord.errors import DiscordException


class BotNotReady(DiscordException):
    def __init__(self):
        super().__init__("Bot is not ready")
