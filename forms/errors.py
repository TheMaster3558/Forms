from __future__ import annotations

import traceback
from typing import TYPE_CHECKING

import discord
from discord.ext import commands

from .constants import ERROR_COLOR

if TYPE_CHECKING:
    from .bot import FormsBot


async def error_handler(
    ctx: commands.Context[FormsBot], error: commands.CommandError
) -> None:
    if isinstance(error, commands.MissingPermissions):
        missing_perms = ', '.join(
            perm.replace('_', ' ').capitalize() for perm in error.missing_permissions
        )
        embed = discord.Embed(
            title='Missing Permissions',
            description=f'You need to have `{missing_perms}`.',
            color=ERROR_COLOR,
        )
        await ctx.send(embed=embed, ephemeral=True)
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send_help(ctx.command)
    elif isinstance(error, commands.BadArgument):
        await ctx.send(str(error), ephemeral=True)
    else:
        embed = discord.Embed(
            title='An unexpected error occurred!',
            description='It has been reported.',
            color=ERROR_COLOR
        )
        await ctx.send(embed=embed, ephemeral=True)

        formatted = '\n'.join(traceback.format_exception(error))
        embed = discord.Embed(
            title='⚠Error⚠', description=f'```py\n{formatted}\n```', color=ERROR_COLOR
        )
        await ctx.bot.error_channel.send(embed=embed)


async def setup(bot: FormsBot) -> None:
    bot.add_listener(error_handler, 'on_command_error')
