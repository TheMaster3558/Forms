from __future__ import annotations

from typing import TYPE_CHECKING

from .forms import FormView
from .questions import QuestionsView
from .permissions import PermissionsView
from ..database import get_forms, get_questions

if TYPE_CHECKING:
    from ..bot import FormsBot


async def add_persistent_views(bot: FormsBot) -> None:
    pool = bot.pool

    for form in await get_forms(pool):
        items = [item async for _, item in get_questions(pool, form_id=form['form_id'])]
        view = FormView(
            items, finishes_at=form['finishes_at'].timestamp(), loop=bot.loop
        )
        bot.add_view(view, message_id=form['form_id'])


async def setup(bot: FormsBot) -> None:
    await add_persistent_views(bot)
