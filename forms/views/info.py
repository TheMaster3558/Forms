from typing import Iterable

import discord


class LinksView(discord.ui.View):
    links: Iterable[tuple[str, str]] = [
        ('Documentation', 'https://formsdiscordbot.readthedocs.io/')
    ]

    def __init__(self):
        super().__init__()

        for label, url in self.links:
            button = discord.ui.Button(label=label, url=url)
            self.add_item(button)
