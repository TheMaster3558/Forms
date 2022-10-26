from __future__ import annotations

import argparse
import asyncio

import discord

from .bot import FormsBot


def main() -> None:
    parser = argparse.ArgumentParser(prog="forms")
    parser.add_argument(
        "-l",
        "--logging",
        help="Whether to setup logging",
        default=True,
        dest="logging",
        action="store_true",
    )
    args = parser.parse_args()

    if args.logging:
        discord.utils.setup_logging()

    bot = FormsBot()
    asyncio.run(bot.start())


if __name__ == "__main__":
    main()
