class Player:
    xp: int = 0
    guild_id: str
    user_id: str
    level: int = 0

    def __init__(self, guild_id: str, user_id: str, xp: int = 0):
        self.xp = xp
        self.guild_id = guild_id
        self.user_id = user_id
        self.level = 0