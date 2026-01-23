from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from sqlalchemy import select
import logging

from app.account.auth import create_email_verification_token, verify_email_token_and_get_user_id, verify_password
from app.account.schemas import UserCreate, UserLogin, UserOut
from app.account.models import User
from app.account.db_commits import database_commit, db_get_one


# LOGGING
logger = logging.getLogger(__name__)


# CREATE USER 
async def create_user(session: AsyncSession, user_in: UserCreate) -> UserOut:
    stmt = select(User).where(User.email == user_in.email)
    
    # 1. Check karein ke user pehle se hai ya nahi
    existing_user = await db_get_one(session, stmt)

    # 2. Agar user mil gaya, toh register NAHI karne dena (400 Bad Request)
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    
    # 3. Agar nahi mila (which is good for registration), toh naya user banayein
    user_data = user_in.to_db_dict()
    new_user = User(**user_data)
    
    session.add(new_user)
    await database_commit(session, new_user)
    
    return new_user

# Authenticate USER
async def authenticate_user(session: AsyncSession, user_login: UserLogin):
    stmt = select(User).where(User.email == user_login.email)

    existing_user =  await db_get_one(session, stmt)

    if not existing_user or not verify_password(user_login.password, existing_user.hashing_password):
        return None
    
    if not existing_user.is_active:
        # Aap chahen toh None return karein ya custom Exception raise karein
        logger.info(f"Login attempt for deactivated user: {existing_user.email}")
        return None
    

    return existing_user


# send Email verification 

async def email_verification_send(user: User):
    token = create_email_verification_token(user.id)
    link = f"http://localhost:8000/account/verify?token={token}"
    print(f"Verify your email: {link}")
    return {"message": "Verification email sent"}



async def verify_email_token(session: AsyncSession, token: str):
    user_id = verify_email_token_and_get_user_id(token, 'verify_email') 


    if not user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid or expired token")
    
    stmt = select(User).where(User.id == user_id)
    user = await db_get_one(session, stmt)

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User Not Found")
    
    user.is_verified = True

    session.add(user)
    await database_commit(session, user)
    return {"msg": "Email is successfully Verified."}





