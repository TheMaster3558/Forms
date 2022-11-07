from __future__ import annotations

from typing import TYPE_CHECKING, Iterable

import discord

if TYPE_CHECKING:
    from ..bot import FormsBot


class LinksView(discord.ui.View):
    links: Iterable[tuple[str, str]] = [
        ('Website', 'website_url'),
        ('Invite', 'invite_url'),
    ]

    def __init__(self, bot: FormsBot):
        super().__init__()

        for label, attr in self.links:
            button = discord.ui.Button(label=label, url=getattr(bot, attr))
            self.add_item(button)
