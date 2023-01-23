import random
from datetime import datetime

import discord

from lib.bot import Bot


class Pagination(discord.ui.View):
    ctx: discord.Interaction

    def __init__(self, *,
                 bot: Bot,
                 timeout: int = 60,
                 ephemeral: bool = False) -> None:
        self.bot = bot
        self.ephemeral = ephemeral

        self.pages = None
        self.message = None
        self.current_page = None
        self.total_page_count = None

        super().__init__(timeout=timeout)

    async def start(self, ctx: discord.Interaction, pages: list[discord.Embed]):

        for embed in pages:
            if not isinstance(embed.colour, discord.Colour):
                color = int("0x" + ''.join([random.choice('0123456789ABCDEF') for j in range(6)]), 16)
                embed.colour = color
            embed.set_footer(text="Made by Gccody")
            embed.timestamp = datetime.now()

        self.pages = pages
        self.total_page_count = len(pages)
        self.ctx: discord.Interaction = ctx
        self.current_page = 0
        if self.total_page_count == 1:
            self.next.disabled = True
            self.previous.disabled = True

        self.counter.label = f'{1}/{self.total_page_count}'

        await self.bot.send(ctx, embed=self.pages[0], view=self,
                            ephemeral=self.ephemeral)

    def handle_buttons(self):
        self.first.disabled = self.current_page <= 1
        self.last.disabled = self.current_page >= self.total_page_count - 2
        self.previous.disabled = self.current_page == 0
        self.next.disabled = self.current_page == self.total_page_count - 1

    @discord.ui.button(emoji=discord.PartialEmoji(name="\U000023ee"), disabled=True)
    async def first(self, interaction: discord.Interaction, button: discord.Button):
        if interaction.user != self.ctx.user:
            embed = discord.Embed(description="You cannot control this pagination because you did not execute it.",
                                  color=discord.Colour.red())
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        self.current_page = 0
        self.handle_buttons()
        self.counter.label = f"{self.current_page + 1}/{self.total_page_count}"
        await interaction.response.edit_message(embed=self.pages[self.current_page], view=self)

    @discord.ui.button(emoji=discord.PartialEmoji(name="\U000025c0"), disabled=True)
    async def previous(self, interaction: discord.Interaction, button: discord.Button):
        if interaction.user != self.ctx.user:
            embed = discord.Embed(description="You cannot control this pagination because you did not execute it.",
                                  color=discord.Colour.red())
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        self.current_page -= 1
        self.handle_buttons()
        self.counter.label = f"{self.current_page + 1}/{self.total_page_count}"
        await interaction.response.edit_message(embed=self.pages[self.current_page], view=self)

    @discord.ui.button(label='', disabled=True)
    async def counter(self, interaction: discord.Interaction, button: discord.Button):
        pass

    @discord.ui.button(emoji=discord.PartialEmoji(name="\U000025b6"))
    async def next(self, interaction: discord.Interaction, button: discord.Button):
        if interaction.user != self.ctx.user:
            embed = discord.Embed(description="You cannot control this pagination because you did not execute it.",
                                  color=discord.Colour.red())
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        self.current_page += 1
        self.handle_buttons()
        self.counter.label = f"{self.current_page + 1}/{self.total_page_count}"
        await interaction.response.edit_message(embed=self.pages[self.current_page], view=self)

    @discord.ui.button(emoji=discord.PartialEmoji(name="\U000023ed"))
    async def last(self, interaction: discord.Interaction, button: discord.Button):
        if interaction.user != self.ctx.user:
            embed = discord.Embed(description="You cannot control this pagination because you did not execute it.",
                                  color=discord.Colour.red())
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        self.current_page = self.total_page_count - 1
        self.handle_buttons()
        self.counter.label = f"{self.current_page + 1}/{self.total_page_count}"
        await interaction.response.edit_message(embed=self.pages[self.current_page], view=self)

    async def on_timeout(self) -> None:
        self.clear_items()
        self.add_item(self.counter)
        await self.ctx.edit_original_response(embed=self.pages[self.current_page], view=self)
