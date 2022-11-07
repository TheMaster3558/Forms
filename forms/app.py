from aiohttp import web


async def handler(request: web.Request) -> None:
    raise web.HTTPFound('/docs/index.html')


def get_app() -> web.Application:
    app = web.Application()
    app.add_routes(
        [
            web.static('/docs/', './docs/_build/html/'),
            web.get('/', handler),
        ]
    )
    return app
