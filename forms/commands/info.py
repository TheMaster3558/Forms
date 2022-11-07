from __future__ import annotations

from typing import TYPE_CHECKING

import discord
from discord.ext import commands

from ..constants import COLOR
from ..views import LinksView

if TYPE_CHECKING:
    from ..bot import FormsBot


@commands.hybrid_command(name='info', description='Get information about the bot.')
async def info_command(ctx: commands.Context[FormsBot]) -> None:
    embed = discord.Embed(
        title=f'{ctx.bot.user.name}',
        description=ctx.bot.description,
        timestamp=discord.utils.utcnow(),
        color=COLOR,
    )
    embed.set_thumbnail(url=ctx.bot.user.avatar.url)
    embed.add_field(name='Creator', value=ctx.bot.application.owner.name)
    embed.add_field(
        name='Bot Created',
        value=discord.utils.format_dt(ctx.bot.user.created_at, style='R'),
    )

    view = LinksView(ctx.bot)
    await ctx.send(embed=embed, view=view if view.children else None)
