from typing import Iterable

import discord

from ..constants import DOCS_LINK, INVITE_URL


class LinksView(discord.ui.View):
    links: Iterable[tuple[str, str]] = [
        ('Documentation', DOCS_LINK),
        ('Invite', INVITE_URL),
    ]

    def __init__(self):
        super().__init__()

        for label, url in self.links:
            button = discord.ui.Button(label=label, url=url)
            self.add_item(button)
