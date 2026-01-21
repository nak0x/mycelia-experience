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
        self._sphero_impact = False
        self._balance_toggle = False
        self._interaction_2_done = False

    async def on_sphero_impact(self, frame: Frame, ws: web.WebSocketResponse) -> None:
        if frame.value == True:
            self._sphero_impact = True
            print(f"[WS] Sphero impact set to True")
        await self._check_interaction_2(ws)

    async def on_balance_toggle(self, frame: Frame, ws: web.WebSocketResponse) -> None:
        if frame.value == True:
            self._balance_toggle = True
            print(f"[WS] Balance toggle set to True")
        await self._check_interaction_2(ws)

    async def _check_interaction_2(self, ws: web.WebSocketResponse) -> None:
        if self._interaction_2_done:
            return

        if self._sphero_impact and self._balance_toggle:
            self._interaction_2_done = True
            print("[WS] Interaction condition met! Broadcasting 02-interaction-done")
            Timer(10000, self.send_02_interaction_done, autostart=True)

    def send_02_interaction_done(self):
        asyncio.run(self.hub.broadcast_action("02-interaction-done", True))
            
    async def on_reset(self, frame: Frame, ws: web.WebSocketResponse) -> None:
        print(f"Reset interaction 2")
        self._reset()