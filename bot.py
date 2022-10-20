import discord
from discord import app_commands
from discord.ext import commands


class FormsBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(command_prefix=[], intents=intents)
        
