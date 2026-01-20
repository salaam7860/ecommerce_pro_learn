from datetime import timedelta, datetime, timezone
from passlib.context import CryptContext
from decouple import config
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from jose import jwt
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