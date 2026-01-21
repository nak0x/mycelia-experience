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
        ws_dispatcher = self.app["ws_dispatcher"]
        if ws_dispatcher is not None:
            controller = ws_dispatcher._get_controller("app.ws_controllers.first_interaction.Controller")
            if controller is not None:
                await controller.on_reset(frame, ws)

            controller = ws_dispatcher._get_controller("app.ws_controllers.second_interaction.Controller")
            if controller is not None:
                await controller.on_reset(frame, ws)

            controller = ws_dispatcher._get_controller("app.ws_controllers.third_interaction.Controller")
            if controller is not None:
                await controller.on_reset(frame, ws)

        await self.hub.broadcast_action("01-reset", None)
        await self.hub.broadcast_action("02-reset", None)
        await self.hub.broadcast_action("03-reset", None)