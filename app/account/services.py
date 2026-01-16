from app.account.models import User
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status


# CREATE USER 
async def create_user(session: AsyncSession, user: User):
    stmt = select(User).where(User.id == user.id)
    result = session.scalars(stmt)
    if not result:
        new_user = User(
            id= user.id,
            email=user.email,
            hashing_password=user.hashing_password
        )
        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)
    return new_user