from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field

class RegisterUser(BaseModel):
    firstName: str
    lastName: str
    username: str
    email: EmailStr
    password: str

class LoginUser(BaseModel):
    usernameOrEmail: str
    password: str

class UserMessage(BaseModel):
    message: str

class PasswordResetRequest(BaseModel):
    email: EmailStr
    username: str

class PasswordResetConfirm(BaseModel):
    email: EmailStr
    new_password: str
