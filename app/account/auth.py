from jose import jwt, ExpiredSignatureError, JWTError
from datetime import timedelta, datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import MultipleResultsFound
from fastapi import HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, SQLAlchemyError 
from passlib.context import CryptContext
from sqlalchemy import select
from decouple import config
from uuid import uuid4

from app.account.db_commits import database_commit, db_get_one
from app.account.models import RefreshToken, User
from app.account.log_config import logger



JWT_ACCESS_TOKEN_TIME_MIN = config("JWT_ACCESS_TOKEN_TIME_MIN", cast=int)
JWT_ACCESS_TOKEN_TIME_DAY = config("JWT_ACCESS_TOKEN_TIME_DAY", cast=int)
EMAIL_VERIFICATION_TOKEN_TIME_HOUR= config("EMAIL_VERIFICATION_TOKEN_TIME_HOUR", cast=int)
PASSWORD_RESET_TOKEN= config("PASSWORD_RESET_TOKEN", cast=int)
JWT_SECRET_KEY = config("JWT_SECRET_KEY")
JWT_ALGORITHM = config("JWT_ALGORITHM")


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str):
    return pwd_context.hash(password)



def verify_password(plain_password: str, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

async def get_single_result(session: AsyncSession, stmt):
    try:
        result = await session.scalars(stmt)
        return result.one_or_none()
    except MultipleResultsFound:
        logger.error("Multiple results found for a unique qurery.")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database consistency error.")
    except SQLAlchemyError:
        logger.exception("Database fetch error")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error occured." )


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
            "refresh_token": refresh_token_str,
            "token_type": "bearer"
        }
    except IntegrityError as e:
        await session.rollback()
        print(f"Database Integrity hit: {e}")
        raise None
    
def decode_token(token: str):
    try:
        # 1. Algorithms ko list mein rakha
        # 2. Key aur token ko print karke verify karein
        # JWT decode karte waqt logger use karna
        logger.debug(f"Decoding JWT token: {token}")
        return jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except ExpiredSignatureError as e:
        logger.warning(f"Token expired: {str(e)}")
        raise HTTPException(status_code=401, detail="Token has Expired.")
    except Exception as e:
        # Yahan logger error message log karega
        logger.error(f"JWT Decode Error Type: {type(e).__name__}")
        logger.error(f"JWT Decode Error Message: {str(e)}")
        raise HTTPException(status_code=401, detail=f"Invalid Token: {str(e)}")
    

# REFRESH TOKEN


    
async def verify_refresh_token(session: AsyncSession, token: str):

    stmt = select(RefreshToken).where(RefreshToken.token == token)
    db_token = await get_single_result(session, stmt)
    
    if not db_token or db_token.revoked:
        return None
    expires_at = db_token.expires_at

    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if expires_at > datetime.now(timezone.utc):
        user_stmt = select(User).where(User.id == db_token.user_id)
        return await get_single_result(session, user_stmt)
    return None
  
# CREATE EMAIL VERIFICATION TOKEN
def create_email_verification_token(user_id: int):
    expire = datetime.now(timezone.utc) + timedelta(hours=EMAIL_VERIFICATION_TOKEN_TIME_HOUR)
    encode = {"sub": str(user_id), "type": "verify_email", "exp": expire}
    return jwt.encode(encode, JWT_SECRET_KEY, JWT_ALGORITHM)


# VERIFY EMAIL TOKEN AND GET USER ID 
def verify_email_token_and_get_user_id(token: str, token_type: str):
    # DECODE THE TOKEN
    payload = decode_token(token)

    print(payload)

    if not payload or payload.get("type") != token_type:
        return None
   
    return int(payload.get("sub"))

# CREATE TOKEN FOR PASSWORD RESET 
def password_reset_token(user_id: int):
    expire = datetime.now(timezone.utc) + timedelta(hours=PASSWORD_RESET_TOKEN)
    encode = {
        "sub": str(user_id),
        "exp": expire,
        "type": "password_reset"
    }
    return jwt.encode(encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

async def revoke_refresh_token(session: AsyncSession, token: str):
    stmt = select(RefreshToken).where(RefreshToken.token==token)
    db_token = await db_get_one(session, stmt)

    if db_token:
        db_token.revoked = True
        await database_commit(session, db_token)
        





















