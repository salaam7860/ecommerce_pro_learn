from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from sqlalchemy import select
import logging

from app.account.auth import create_email_verification_token, hash_password, password_reset_token, verify_email_token_and_get_user_id, verify_password
from app.account.schemas import ForgetPasswordReset, PasswordChangeRequest, PasswordResetNew, UserCreate, UserLogin, UserOut
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

async def email_verification_send(session: AsyncSession, user: User):
    stmt = select(User).where(User.id == user.id)
    user = await db_get_one(session, stmt)

    if user.is_verified:
        logger.info(f"User id: {user.id} attempted verification but is already verified.")
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"User_id: {user.id}, Email is already Verified.")

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

# CHANGE PASSWORD
async def change_password(session: AsyncSession, user: User, data: PasswordChangeRequest):

    if not verify_password(data.old_password, user.hashing_password):
        logger.warning("Incorrect password", extra={"user_id": user.id})
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Password isn't correct.")

    if verify_password(data.new_password, user.hashing_password):
        logger.warning("Same password as old.", extra={"user_id": user.id})
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="New password must be different.")

    user.hashing_password = hash_password(data.new_password)

    session.add(user)

    await database_commit(session, user)

    return {"Message": f"User: {user.id}, The password has been renewed"}




# FORGET PASSWORD
async def password_reset(session: AsyncSession, data: ForgetPasswordReset):
    stmt = select(User).where(User.email == data.email)
    user = await db_get_one(session, stmt)

    if not user:
        logger.warning(f"Invalid Email")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid Email")
    
    token = password_reset_token(user.id)
    link = f"http://localhost:8000/account/verify?Password_Reset={token}"
    print(f'Reset Your Password: {link}')
    return {"msg": "Link for reset password has been sent."}

# VERIFY PASSWORD RESET TOKEN
async def verify_password_token(session: AsyncSession, data: PasswordResetNew):
    user_id =  verify_email_token_and_get_user_id(data.token, "password_reset")

    if not user_id:
        logger.warning("Token Invalid or Expired Token")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token Invalid or Expired Token")
    
    stmt = select(User).where(User.id == user_id)
    user = await db_get_one(session, stmt)

    if not user:
        logger.warning("User not Found.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not Found.")
    
    user.hashing_password = hash_password(data.new_password)

    session.add(user)
    await database_commit(session, user)
    
    return {"msg": "Password has been reset."}



