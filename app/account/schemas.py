from pydantic import BaseModel, EmailStr, Field




class UserBase(BaseModel):
    email: EmailStr 
    is_active: bool = True
    is_admin: bool = False
    is_verified: bool = False


class UserCreate(UserBase):
    password: str = Field(min_length=3)