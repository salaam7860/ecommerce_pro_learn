from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator
import string

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


class UserLoggedIn(BaseModel):
    id: int
    email: EmailStr
    loggedin: bool = False

    @model_validator(mode="after")
    def checked_loggedin(self):
        if self.id is not None and self.id > 0 and self.email is not None:
            self.loggedin = True
        else:
            self.loggedin = False
        return self
    
class PasswordChangeRequest(BaseModel):
    old_password: str = Field(...)
    new_password: str = Field(..., min_length=3) 


    @field_validator("new_password")
    @classmethod
    def validate_new_password_strength(cls, value: str) ->str:
        if value.lower() == value or value.upper() == value:
            raise ValueError("Password must contain both uppercase and lowercase letters")
        if not any(char.isdigit() for char in value):
            raise ValueError("Password must contain at least one digit")
        if not any(char in string.punctuation for char in value):
            raise ValueError("Your password must contain at least one special character")
        return value
    

class ForgetPasswordReset(BaseModel):
    email: EmailStr


class PasswordResetNew(BaseModel):
    token: str
    new_password: str = Field(..., min_length=3)


    @field_validator("new_password")
    @classmethod
    def validate_new_password_strength(cls, value: str) ->str:
        if value.lower() == value or value.upper() == value:
            raise ValueError("Password must contain both uppercase and lowercase letters")
        if not any(char.isdigit() for char in value):
            raise ValueError("Password must contain at least one digit")
        if not any(char in string.punctuation for char in value):
            raise ValueError("Your password must contain at least one special character")
        return value