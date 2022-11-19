import argparse
import asyncio

import discord

from .bot import FormsBot


def main() -> None:
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
        action='store_true',
    )
    parser.add_argument(
        '-g',
        '--gateway',
        help='Whether to the Discord Gateway',
        default=False,
        dest='gateway',
        action='store_true',
    )
    parser.add_argument(
        '-n',
        '--use-ngrok',
        help='Whether to start a ngrok tunnel with the web server',
        default=False,
        dest='ngrok',
        action='store_true',
    )
    args = parser.parse_args()

    if args.logging:
        discord.utils.setup_logging()

    bot = FormsBot()
    bot.use_ngrok = args.ngrok

    if args.web and args.gateway:
        raise TypeError('Cannot use both --web and --gateway')

    if args.web:
        asyncio.run(bot.run_with_web())
    else:
        asyncio.run(bot.run_with_gateway())


if __name__ == '__main__':
    main()
