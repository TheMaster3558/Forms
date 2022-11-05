import traceback
from typing import TYPE_CHECKING

import discord
from discord.ext import commands

if TYPE_CHECKING:
    from .bot import FormsBot


async def error_handler(ctx: commands.Context[FormsBot], error: commands.CommandError) -> None:
    channel: discord.abc.Messageable = ctx.channel

    if isinstance(error, commands.MissingPermissions):
        missing_perms = ', '.join(perm.replace('_', ' ').capitalize() for perm in error.missing_permissions)
        embed = discord.Embed(
            title='Missing Permissions',
            description=f'You need to have `{missing_perms}`.'
        )
    else:
        channel = ctx.bot.error_channel
        embed = discord.Embed(
            title='⚠Error⚠',
            description=f'```py\n{traceback.format_exception(error)}\n```'
        )

    embed.color = discord.Color.red()
    await channel.send(embed=embed)


async def setup(bot: FormsBot) -> None:
    bot.add_listener(error_handler, 'on_command_error')
