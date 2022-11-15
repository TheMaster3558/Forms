from __future__ import annotations

from typing import TYPE_CHECKING

from .forms import form_create_command, form_finish_command, take_form_command
from .info import info_command
from .reports import report_command

if TYPE_CHECKING:
    from ..bot import FormsBot


async def setup(bot: FormsBot) -> None:
    bot.tree.add_command(form_create_command)
    bot.tree.add_command(form_finish_command)
    bot.tree.add_command(take_form_command)
    bot.tree.add_command(info_command)
    bot.tree.add_command(report_command)
