from fastapi import HTTPException, status, Request
from sqlalchemy import select
from sqlalchemy.exc import MultipleResultsFound

from app.account.auth import decode_token
from app.db.config import SessionDep
from app.account.models import User

def not_data(token):
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing access token", headers={"WWW-Authenticate": "Bearer"})
def not_refresh_token(token):
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Refresh token")
    
async def user_extract(session: SessionDep, user_id):
    try:
        stmt = select(User).where(User.id == int(user_id))
        result = await session.scalars(stmt)
        user = result.one_or_none()
    except MultipleResultsFound:
        # Agar ek se zyada rows mil gayi hain
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="⚠️ Multiple users found for this id!")
    
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User Not Found")
    
    return  user





async def is_authenticated(session: SessionDep, request: Request):
    token = request.cookies.get("access_token")

    # Validate the token is their or missing 
    not_data(token)
    
    # decode the token
    payload = decode_token(token)

    # Validate the payload is their or missing 
    not_data(payload)

    # extract the user id 
    user_id = payload.get("sub")

    # Validate the payload is their or missing 
    not_data(user_id)
    

    # match and extract the user from the database 
    user = await user_extract(session, user_id)

    return user


