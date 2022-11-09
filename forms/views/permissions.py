from typing import TYPE_CHECKING, Self

import discord

if TYPE_CHECKING:
    from .._types import Interaction


class PermissionsView(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=600)
        self.users: list[int] = []
        self.roles: list[int] = []
        self.everyone: bool = False

    def is_done(self) -> bool:
        return self.select_users.disabled and self.select_roles.disabled

    async def disable_all(self, message: discord.Message) -> None:
        self.allow_everyone.disabled = True
        self.select_users.disabled = True
        self.select_roles.disabled = True
        await message.edit(view=self)

    @discord.ui.button(label='Allow Everyone')
    async def allow_everyone(
        self, interaction: Interaction, button: discord.ui.Button
    ) -> None:
        await interaction.response.send_message('Everyone can take this form.')
        self.everyone = True
        await self.disable_all(interaction.message)
        self.stop()

    @discord.ui.select(cls=discord.ui.UserSelect, min_values=0, max_values=25)
    async def select_users(
        self, interaction: Interaction, select: discord.ui.UserSelect[Self]
    ) -> None:
        await interaction.response.defer()
        self.users = [user.id for user in select.values]

        self.select_users.disabled = True
        await interaction.message.edit(view=self)

        if self.is_done():
            await self.disable_all(interaction.message)
            self.stop()

    @discord.ui.select(cls=discord.ui.RoleSelect, min_values=0, max_values=25)
    async def select_roles(
        self, interaction: Interaction, select: discord.ui.RoleSelect[Self]
    ) -> None:
        await interaction.response.defer()
        self.roles = [role.id for role in select.values]

        self.select_roles.disabled = True
        await interaction.message.edit(view=self)

        if self.is_done():
            await self.disable_all(interaction.message)
            self.stop()
