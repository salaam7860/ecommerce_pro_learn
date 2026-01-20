from pydantic import BaseModel, EmailStr, Field, model_validator

from app.account.auth import hash_password




class UserBase(BaseModel):
    email: EmailStr 
    is_active: bool = True
    is_admin: bool = False
    is_verified: bool = False


class UserCreate(UserBase):
    password: str = Field(min_length=3)

    # It hashes the password and renames the key
    def to_db_dict(self):
        user_data = self.model_dump()

        password_plain = user_data.pop("password", None)

        if password_plain:
            user_data['hashing_password'] = hash_password(password_plain)
        return user_data
    
class UserOut(BaseModel):
    id: int 
    created: bool = False
    model_config = {"from_attributes": True}


    @model_validator(mode="after")
    def check_if_created(self)->"UserOut":
        if self.id is not None and self.id > 0:
            self.created = True
        else:
            self.created = False
        return self



class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=3)