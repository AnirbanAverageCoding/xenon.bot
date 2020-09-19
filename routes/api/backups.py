from sanic import Blueprint, response
import msgpack
import json

from stay_fast import *
from auth import *


bp = Blueprint(name="api.backups", url_prefix="/backups")


@bp.get("/ids")
@requires_bot_token()
@ratelimit(limit=30, seconds=10, level=RequestBucket.TOKEN)
@cache_response(respect_query=True, minutes=1)
async def get_ids(request, _):
    query = request.args
    source_id = query.get("source")
    target_id = query.get("target")

    backup_id = query.get("backup")
    if backup_id is not None:
        backup = await request.app.db.backups.find_one({"_id": backup_id}, projection={"data.id": True})
        if backup is not None:
            source_id = backup["data"]["id"]

    translator = await request.app.db.id_translators.find_one({"source_id": source_id, "target_id": target_id})

    if translator is not None:
        del translator["_id"]
        return response.json(translator)

    else:
        return response.json({"error": "No id translator found"}, status=404)


@bp.websocket("/loaders/ws")
@requires_bot_token()
@ratelimit(limit=1, seconds=1, level=RequestBucket.TOKEN)
async def ws_loaders(request, _, ws):
    async for _, msg in request.app.subscriber.psubscribe("loaders:*"):
        event = msg[0].decode("utf-8")[len("loaders:"):]
        data = msgpack.unpackb(msg[1])
        await ws.send(json.dumps({
            "event": event,
            "data": data
        }))
