from __future__ import annotations

import argparse
import asyncio
import sys

import discord

from .bot import FormsBot


def main() -> int:
    parser = argparse.ArgumentParser(prog='forms')
    parser.add_argument(
        '-l',
        '--logging',
        help='Whether to setup logging',
        default=True,
        dest='logging',
        action='store_true',
    )
    parser.add_argument(
        '-w',
        '--web',
        help='Whether to use aiointeractions.InteractionsApp',
        default=False,
        dest='web',
        action='store_true'
    )
    parser.add_argument(
        '-g',
        '--gateway',
        help='Whether to the Discord Gateway',
        default=True,
        dest='gateway',
        action='store_true'
    )
    args = parser.parse_args()

    if args.logging:
        discord.utils.setup_logging()

    bot = FormsBot()

    if args.web and args.gateway:
        raise TypeError('Cannot use both --web and --gateway')

    if args.web:
        asyncio.run(bot.start_with_web())
    else:
        asyncio.run(bot.start_with_gateway())
    return 0


if __name__ == '__main__':
    sys.exit(main())
