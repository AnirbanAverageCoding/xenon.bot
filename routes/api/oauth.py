from sanic import Blueprint, response
import aiohttp

from oauth import requires_token
from helpers import requires_body


bp = Blueprint(name="api.oauth", url_prefix="/oauth")


@bp.post("/token")
@requires_body("code")
async def exchange_token_route(request):
    data = request.json
    authorization_code = data["code"]

    try:
        token_data = await request.app.token_exchange(code=authorization_code)
    except aiohttp.ClientResponseError as e:
        return response.text(e.message, status=e.status)

    try:
        user = await request.app.oauth_get_user(token=token_data["access_token"])
    except aiohttp.ClientResponseError as e:
        return response.text(e.message, status=e.status)

    jwt_token = request.app.make_jwt_token(user["id"], token_data)
    return response.json({"token": jwt_token})


@bp.get("/user")
@requires_token(user_only=True)
async def get_user_route(request, user):
    try:
        data = await request.app.oauth_get_user(token=user.access_token)
    except aiohttp.ClientResponseError as e:
        return response.text("Discord api error", status=e.status)

    return response.json(data)


@bp.get("/guilds")
@requires_token(user_only=True)
async def get_guilds_route(request, user):
    try:
        data = await request.app.oauth_get_guilds(token=user.access_token)
    except aiohttp.ClientResponseError as e:
        return response.text("Discord api error", status=e.status)

    return response.json(data)


@bp.get("/token")
@requires_token(user_only=True)
async def get_token_route(request, user):
    return response.json({
        "access_token": user.access_token,
        # The integration token does not include oauth credentials
        "integration_token": request.app.make_jwt_token(user.id)
    })
