from fastapi import Depends, HTTPException, status, Request
from sqlalchemy import select
from sqlalchemy.exc import MultipleResultsFound
from jose import ExpiredSignatureError

from app.account.auth import decode_token
from app.db.config import SessionDep
from app.account.models import User
from app.account.log_config import logger
from app.account.db_commits import db_get_one

def not_data(token):
    if not token:
        logger.warning("Authentication failed: missing access token")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing access token", headers={"WWW-Authenticate": "Bearer"})
def not_refresh_token(token):
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Refresh token")
    
async def user_extract(session: SessionDep, user_id):
    try:
        stmt = select(User).where(User.id == int(user_id))
        user = await db_get_one(session, stmt)

    except MultipleResultsFound:
        # Agar ek se zyada rows mil gayi hain
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="⚠️ Multiple users found for this id!")
    
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User Not Found")
    
    return  user





async def is_authenticated(session: SessionDep, request: Request):
    token = request.cookies.get("access_token")

    if not token:
        logger.warning("Authentication failed: missing access token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing access token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_token(token)

    # If decode_token returned None => invalid or expired
    if not payload:
        logger.warning("Access token invalid or expired")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token"
        )

    user_id = payload.get("sub")
    if not user_id:
        logger.error("Token payload missing ‘sub’ claim")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed access token"
        )

    user = await user_extract(session, user_id)
    logger.info(f"Authenticated user {user.id}")
    return user


async def require_admin(user: User = Depends(is_authenticated)):
    if not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return user
     