from discord.app_commands.errors import AppCommandError


class BotNotReady(AppCommandError):
    def __init__(self):
        super().__init__("Bot is not ready")
