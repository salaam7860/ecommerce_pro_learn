from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status

from app.account.auth import verify_password
from app.account.models import User
from app.account.schemas import UserCreate, UserLogin, UserOut


# CREATE USER 
async def create_user(session: AsyncSession, user: UserCreate)->UserOut:
    stmt = select(User).where(User.email == user.email)
    result = await session.scalars(stmt)
    existing_user = result.one_or_none()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already exist!!!.")
    # new_user = User(email=user.email,hashing_password=hash_password(user.password))
    gen_user= user.to_db_dict()
    new_user = User(**gen_user)

    session.add(new_user)

    try: 
        await session.commit()
        await session.refresh(new_user)
        return new_user
    
    except IntegrityError as e:
        await session.rollback()
        print(f"Database integrity hit: {e}")
        raise None


async def authenticate_user(session: AsyncSession, user_login: UserLogin):
    stmt = select(User).where(User.email == user_login.email)
    result = await session.scalars(stmt)
    existing_user = result.one_or_none()

    if not existing_user or not verify_password(user_login.password, existing_user.hashing_password):
        return None
    return existing_user

