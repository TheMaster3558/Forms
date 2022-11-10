from __future__ import annotations

from typing import TYPE_CHECKING, Any

import discord
from discord import app_commands
from discord.ext import commands

from ..constants import COLOR
from ..views import LinksView

if TYPE_CHECKING:
    from ..bot import FormsBot


class HelpCommand(commands.HelpCommand):
    context: commands.Context[FormsBot]

    def __init__(self):
        super().__init__(
            command_attrs={'description': 'The help command for this bot.'}
        )

    async def send_error_message(self, error: str) -> None:
        await self.context.send(error)

    async def send_bot_help(self, _: Any) -> None:
        embed = discord.Embed(
            title=f'{self.context.bot.user.name} Help',
            description=self.context.bot.description,
            timestamp=discord.utils.utcnow(),
            color=COLOR,
        )
        for command in self.context.bot.commands:
            embed.add_field(
                name=f'`{self.get_command_signature(command)}`',
                value=f'{self.context.bot.app_commands[command.name].mention} | {command.description}',
                inline=False,
            )

        view = LinksView(self.context.bot)
        await self.context.send(embed=embed, view=view if view.children else None)

    async def send_command_help(
        self, command: commands.Command[None, ..., Any]
    ) -> None:
        embed = discord.Embed(
            title=command.name,
            description=f'```{self.get_command_signature(command)}```',
            timestamp=discord.utils.utcnow(),
            color=COLOR,
        )
        embed.add_field(name='Command Description', value=command.description)
        embed.add_field(
            name='Slash Command',
            value=self.context.bot.app_commands[command.name].mention,
        )
        await self.context.send(embed=embed)


@app_commands.command(name='help', description='Use this command for help!')
@app_commands.describe(command='The command to get help with')
async def help_command(interaction: discord.Interaction, command: str = None) -> None:
    ctx = await commands.Context.from_interaction(interaction)
    help_cmd = ctx.bot.help_command.copy()
    help_cmd.context = ctx
    await help_cmd.command_callback(ctx, command=command)
