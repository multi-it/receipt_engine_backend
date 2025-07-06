from pydantic import BaseModel, Field, EmailStr

class UserRegister(BaseModel):
    fullname: str = Field(min_length=2, max_length=100)
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=6, max_length=128)

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    fullname: str
    username: str
    email: str
    is_active: bool
