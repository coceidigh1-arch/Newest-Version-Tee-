import secrets
from fastapi import Header, HTTPException, Request
from app.config import settings


def get_bearer_or_header_token(
    authorization: str | None,
    x_api_key: str | None,
    x_user_token: str | None = None,
) -> str | None:
    if x_user_token:
        return x_user_token
    if x_api_key:
        return x_api_key
    if authorization and authorization.lower().startswith("bearer "):
        return authorization.split(" ", 1)[1].strip()
    return None


async def require_admin_key(
    request: Request,
    authorization: str | None = Header(default=None),
    x_api_key: str | None = Header(default=None),
):
    if not settings.APP_API_KEY:
        return
    candidate = get_bearer_or_header_token(authorization, x_api_key)
    if not candidate or not secrets.compare_digest(candidate, settings.APP_API_KEY):
        raise HTTPException(status_code=401, detail="Admin API key required")


async def authorize_user_request(
    request: Request,
    user_id: str,
    db,
    authorization: str | None = Header(default=None),
    x_api_key: str | None = Header(default=None),
    x_user_token: str | None = Header(default=None),
):
    admin_token = get_bearer_or_header_token(authorization, x_api_key)
    if settings.APP_API_KEY and admin_token and secrets.compare_digest(admin_token, settings.APP_API_KEY):
        return

    if not settings.USER_AUTH_REQUIRED:
        return

    candidate = get_bearer_or_header_token(authorization, x_api_key, x_user_token)
    if not candidate:
        raise HTTPException(status_code=401, detail="User token required")

    row = await db.execute_fetchone("SELECT api_token FROM users WHERE id = ?", (user_id,))
    if not row or not row["api_token"] or not secrets.compare_digest(candidate, row["api_token"]):
        raise HTTPException(status_code=403, detail="Invalid user token")
