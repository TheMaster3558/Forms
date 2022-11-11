from __future__ import annotations

from typing import TYPE_CHECKING

import discord
from discord import app_commands
from discord.ext import commands

from ..constants import ERROR_COLOR
from ..views import ReportsView

if TYPE_CHECKING:
    from ..bot import FormsBot


@commands.hybrid_command(
    name='report',
    description='Report a bug. This is not a support command.'
)
async def report_command(ctx: commands.Context[FormsBot]) -> None:
    embed = discord.Embed(
        title='Click to Start',
        color=ERROR_COLOR
    )

    view = ReportsView(ctx.author)
    await ctx.send(embed=embed, view=view, ephemeral=True)
    await view.wait()

    embed = discord.Embed(
        title='A report has been submitted',
        description=view.text,
        timestamp=discord.utils.utcnow(),
        color=ERROR_COLOR
    )
    embed.set_author(name=ctx.author, icon_url=ctx.author.display_avatar.url)
    await ctx.bot.reports_channel.send(embed=embed)
