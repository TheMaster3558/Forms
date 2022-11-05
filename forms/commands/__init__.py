from __future__ import annotations

from typing import TYPE_CHECKING

from .forms import form_create_command, form_finish_command, finish_form_context_menu
from .info import info_command

if TYPE_CHECKING:
    from ..bot import FormsBot


async def setup(bot: FormsBot) -> None:
    bot.add_command(form_create_command)
    bot.add_command(form_finish_command)
    bot.tree.add_command(finish_form_context_menu)
    bot.add_command(info_command)
