import discord
from discord import app_commands
from discord.ext import commands


class FormsBot(discord.Client):
    def __init__(self):
        self.tree = app_commands.CommandTree(client)
        
