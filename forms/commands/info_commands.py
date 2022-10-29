import discord
from discord.ext import commands

from .. import __author__
from ..constants import COLOR

import asyncpg
import discord


versions = f'''asyncpg {asyncpg.__version__}
discord.py {discord.__version__}'''


@commands.hybrid_command(
    name='info',
    description='Info about the bot.'
)
async def info_command(ctx: commands.Context) -> None:
    embed = discord.Embed(
        title=f'{ctx.bot.user.name}',
        timestamp=discord.utils.utcnow(),
        color=COLOR
    )
    embed.set_thumbnail(url=ctx.bot.user.avatar.url)
    embed.add_field(
        name='Creator',
        value=__author__
    )
    embed.add_field(
        name='Bot Created',
        value=discord.utils.format_dt(ctx.bot.user.created_at, style='R')
    )
    embed.add_field(
        name='Versions',
        value=versions
    )
    await ctx.send(embed=embed)
