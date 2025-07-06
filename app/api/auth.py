from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database.connection import get_session
from app.database.models import UserModel
from app.domain.schemas.user import UserRegister, UserLogin, UserResponse
from app.domain.schemas.auth import Token
from app.auth.security import hash_password, verify_password, create_access_token, create_refresh_token
from app.domain.entities.user import User

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserRegister,
    session: AsyncSession = Depends(get_session)
):
    stmt = select(UserModel).where(
        (UserModel.username == user_data.username) | 
        (UserModel.email == user_data.email)
    )
    result = await session.execute(stmt)
    existing_user = result.scalar()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered"
        )
    
    user = User(
        full_name=user_data.fullname,
        username=user_data.username,
        email=user_data.email,
        password_hash=hash_password(user_data.password)
    )
    user.validate()
    
    db_user = UserModel(
        full_name=user.full_name,
        username=user.username,
        email=user.email,
        password_hash=user.password_hash
    )
    
    session.add(db_user)
    await session.commit()
    await session.refresh(db_user)
    
    return UserResponse(
        id=db_user.id,
        fullname=db_user.full_name,
        username=db_user.username,
        email=db_user.email,
        is_active=db_user.is_active
    )

@router.post("/login", response_model=Token)
async def login_user(
    user_credentials: UserLogin,
    session: AsyncSession = Depends(get_session)
):
    stmt = select(UserModel).where(UserModel.username == user_credentials.username)
    result = await session.execute(stmt)
    user = result.scalar()
    
    if not user or not verify_password(user_credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is disabled"
        )
    
    access_token = create_access_token({"user_id": user.id, "username": user.username})
    refresh_token = create_refresh_token({"user_id": user.id, "username": user.username})
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer"
    )
