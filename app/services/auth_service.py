from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password, create_access_token
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, UserResponse


async def register_user(db: AsyncSession, data: UserCreate) -> UserResponse:
    existing_user = await db.scalar(select(User).filter_by(email=data.email))
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already exists")

    hashed_password = hash_password(data.password)

    new_user = User(
        fullname=data.full_name,      
        email=data.email,
        hashed_password=hashed_password,
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return UserResponse.model_validate(new_user)


async def login_user(db: AsyncSession, data: UserLogin):
    user = await db.scalar(select(User).filter_by(email=data.email))
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    access_token = create_access_token(user.id)
    return {"access_token": access_token, "token_type": "bearer", "user": UserResponse.model_validate(user)}