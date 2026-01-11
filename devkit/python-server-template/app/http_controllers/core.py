from aiohttp import web
from app.http_controllers.base import HttpController
from app.frames.parser import parse_frame_from_request


class CoreController(HttpController):

    async def health(self, request: web.Request) -> web.Response:
        # Health does not need Frame input, but still returns a Frame-like JSON if you want.
        return web.json_response({
            "ok": True,
            "service": "unified-server"
        })

    async def broadcast(self, request: web.Request) -> web.Response:
        """
        Expects a Frame in HTTP body.
        Broadcasts the exact same validated frame to WS clients.
        """
        try:
            frame = await parse_frame_from_request(request)
        except Exception as e:
            return web.Response(
                text=self.build_frame("00-broadcast", f"error to parse frame: {e}"),
                status=400,
                content_type="application/json"
            )

        sent = await self.hub.broadcast(frame.raw_json)
        return web.json_response(self.build_frame("00-broadcast", sent))
    
    async def get_logs(self, request: web.Request) -> web.Response:
        key = request.query.get("key", None)
        limit = request.query.get("limit", None)
        asc = request.query.get("asc", False)

        if limit is not None:
            try:
                limit = int(limit)
            except Exception:
                return web.Response(
                    text=self.build_frame("00-logs", "limit must be an integer"),
                    status=400,
                    content_type="application/json"
                )
            
        if asc is not None:
            try:
                asc = bool(asc)
            except Exception:
                return web.Response(
                    text=self.build_frame("00-logs", "asc must be a boolean"),
                    status=400,
                    content_type="application/json"
                )
            
        logs = self.logger.get_logs(key, limit, not asc)
        return web.json_response(logs)