from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse

from app.account.schemas import UserCreate, UserOut, UserLogin, UserLoggedIn
from app.account.auth import create_tokens, set_response,verify_refresh_token
from app.account.services import authenticate_user, create_user
from app.account.dependency import not_refresh_token
from app.account.dependency import is_authenticated
from app.db.config import SessionDep
from app.account.models import User


router = APIRouter(prefix="/api/account", tags=["Account"])


@router.post("/register", response_model=UserOut)
async def register(session: SessionDep, user: UserCreate):
    return await create_user(session, user)


@router.post("/login")
async def login(session: SessionDep, user_login: UserLogin):
    user = await authenticate_user(session, user_login)

    if not user: 
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Credentials")
    
    tokens = await create_tokens(session, user)
    
    response = set_response(tokens)

    return response

@router.get("/profile", response_model=UserLoggedIn)
async def profile(user: User = Depends(is_authenticated)):
    return user
    
@router.get("/refresh", response_model=UserLoggedIn)
async def refresh(session: SessionDep, request: Request):
    token = request.cookies.get("refresh_token")

    # Validate the token is their or missing
    not_refresh_token(token)

    user = await verify_refresh_token(session, token)

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")
    
    tokens = await create_tokens(session, user)

    set_response(tokens)

    return user



