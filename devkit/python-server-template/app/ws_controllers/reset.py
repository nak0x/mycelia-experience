from aiohttp import web
from app.ws_controllers.base import WsController
from app.frames.frame import Frame
import asyncio


class Controller(WsController):

    def __init__(self, app: web.Application):
        super().__init__(app)
        
        self._shroom_forest_lighten = False
        self._wind_toggle = False
        self._rain_toggle = False
        self._interaction_1_done = False

    async def on_reset(self, frame: Frame, ws: web.WebSocketResponse) -> None:
        self.hub.broadcast_action("01-reset", None)
        self.hub.broadcast_action("02-reset", None)
        self.hub.broadcast_action("03-reset", None)