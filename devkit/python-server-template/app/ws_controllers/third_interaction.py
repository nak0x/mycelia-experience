from aiohttp import web
from app.ws_controllers.base import WsController
from app.frames.frame import Frame
import asyncio


class Controller(WsController):

    def __init__(self, app: web.Application):
        super().__init__(app)
            
    async def on_reset(self, frame: Frame, ws: web.WebSocketResponse) -> None:
        await self.hub.broadcast_action("03-e-off", None)