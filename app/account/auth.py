from jose import jwt, ExpiredSignatureError, JWTError
from datetime import timedelta, datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import MultipleResultsFound
from fastapi import HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from passlib.context import CryptContext
from sqlalchemy import select
from decouple import config
from uuid import uuid4

from app.account.models import RefreshToken, User



JWT_ACCESS_TOKEN_TIME_MIN = config("JWT_ACCESS_TOKEN_TIME_MIN", cast=int)
JWT_ACCESS_TOKEN_TIME_DAY = config("JWT_ACCESS_TOKEN_TIME_DAY", cast=int)
JWT_SECRET_KEY = config("JWT_SECRET_KEY")
JWT_ALGORITHM = config("JWT_ALGORITHM")


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str):
    return pwd_context.hash(password)



def verify_password(plain_password: str, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)



async def verify_stmt(session: AsyncSession,stmt):
    try:
        result = await session.scalars(stmt)
        data = result.one_or_none()
    except MultipleResultsFound:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="⚠️ Multiple users found for this id!")
    if not data: 
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="⚠️data is Missing")
    return data



# Set Response 
def set_response(tokens):
    response = JSONResponse(content={"message": "Login Successful"})
    response.set_cookie(
        key="access_token",
        value=tokens["access_token"],
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=60*60*24*1
    )
    
    response.set_cookie(
        key="refresh_token",
        value=tokens["refresh_token"],
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=60*60*24*7
    )

    return response


# create access token
def create_access_token(data: dict, expire_delta: timedelta = None):
    to_encode = data.copy()
    expires = datetime.now(timezone.utc) + (expire_delta or timedelta(minutes=JWT_ACCESS_TOKEN_TIME_MIN))
    to_encode.update({"exp": expires})

    return jwt.encode(to_encode, JWT_SECRET_KEY, JWT_ALGORITHM)

async def create_tokens(session: AsyncSession, user: User):
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token_str = str(uuid4())
    expires_at = datetime.now(timezone.utc) + timedelta(days=JWT_ACCESS_TOKEN_TIME_DAY)

    refresh_token = RefreshToken(
        user_id = user.id,
        token = refresh_token_str,
        expires_at = expires_at,

    )
    session.add(refresh_token)

    try: 
        await session.commit()
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
    except IntegrityError as e:
        await session.rollback()
        print(f"Database Integrity hit: {e}")
        raise None
    
def decode_token(token: str):
    try:
        return jwt.decode(token, JWT_SECRET_KEY, algorithms=JWT_ALGORITHM)
    except ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has Expired.")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Token")
    

# REFRESH TOKEN


    
# async def verify_refresh_token(session: AsyncSession, token: str):

#     stmt = select(RefreshToken).where(RefreshToken.token == token)
#     db_token = await verify_stmt(session, stmt)

#     if db_token and not db_token.revoked:
#         expires_at = db_token.expires_at

#         if expires_at.tzinfo is None:
#             expires_at = expires_at.replace(timezone.utc)

#         if expires_at > datetime.now(timezone.utc):
#             user_stmt = select(User).where(User.id == db_token.user_id)
#             user_result = await verify_stmt(session, user_stmt)
#             return user_result
#     return None
  

async def verify_refresh_token(session : AsyncSession, token: str):
  stmt = select(RefreshToken).where(RefreshToken.token == token)
  result = await session.scalars(stmt)
  db_refresh_token = result.first()

  if db_refresh_token and not db_refresh_token.revoked:
    expires_at = db_refresh_token.expires_at
    if expires_at.tzinfo is None:
      expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at > datetime.now(timezone.utc):
      user_stmt = select(User).where(User.id == db_refresh_token.user_id)
      user_result = await session.scalars(user_stmt)
      return user_result.first()
    
  return None