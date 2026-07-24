from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.deps import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, UserResponse
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse)
async def register(data: UserCreate, db: AsyncSession = Depends(get_db)):
    return await auth_service.register_user(db, data)


@router.post("/login")
async def login(
    data: UserLogin,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    result = await auth_service.login_user(db, data)

    response.set_cookie(
        key="access_token",
        value=result["access_token"],
        httponly=True,
        secure=settings.ENVIRONMENT != "development",  # False locally, True in prod
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )

    return {"user": result["user"]}


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("access_token")
    return {"message": "Logged out"}


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)):
    return current_user