from aiohttp import web
from app.ws_controllers.base import WsController
from app.frames.frame import Frame
from app.utils.timer import Timer
import asyncio


class Controller(WsController):

    def __init__(self, app: web.Application):
        super().__init__(app)
        self._reset()
    
    def _reset(self):
        self._shroom_forest_lighten = False
        self._wind_toggle = False
        self._rain_toggle = False
        self._interaction_1_done = False

    async def on_shroom_forest_lighten(self, frame: Frame, ws: web.WebSocketResponse) -> None:
        if frame.value == True:
            self._shroom_forest_lighten = True
            print(f"[WS] Shroom forest lighten set to True")
        await self._check_interaction_1(ws)
    
    async def on_wind_toggle(self, frame: Frame, ws: web.WebSocketResponse) -> None:
        if frame.value == True:
            self._wind_toggle = True
            print(f"[WS] Wind toggle set to True")
        await self._check_interaction_1(ws)
    
    async def on_rain_toggle(self, frame: Frame, ws: web.WebSocketResponse) -> None:
        if frame.value == True:
            self._rain_toggle = True
            print(f"[WS] Rain toggle set to True")
        await self._check_interaction_1(ws)

    async def _check_interaction_1(self, ws: web.WebSocketResponse) -> None:
        if self._interaction_1_done:
            return

        if self._shroom_forest_lighten and self._wind_toggle and self._rain_toggle:
            self._interaction_1_done = True
            print("[WS] Interaction condition met! Broadcasting 01-interaction-done...")
            Timer(10000, self.send_01_interaction_done, autostart=True)

    def send_01_interaction_done(self):
        asyncio.run(self.hub.broadcast_action("01-interaction-done", True))
            

    async def on_reset(self, frame: Frame, ws: web.WebSocketResponse) -> None:
        print(f"Reset interaction 1")
        self._reset()