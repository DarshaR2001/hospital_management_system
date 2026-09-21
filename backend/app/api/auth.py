from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.security import verify_password, get_password_hash, create_access_token
from app.core.dependencies import get_current_user, get_current_active_user
from app.models.auth import User
from app.schemas.auth import LoginRequest, Token, ChangePasswordRequest, UserResponse
from app.services.seed_service import seed_database

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=Token)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    stmt = (
        select(User)
        .where(User.email == payload.email)
        .options(selectinload(User.role))
    )
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive. Please contact administrator.",
        )

    token = create_access_token(
        subject=user.email,
        role=user.role.name,
        user_id=str(user.id),
    )

    return Token(
        access_token=token,
        token_type="bearer",
        role=user.role.name,
        user_id=user.id,
        email=user.email,
        full_name=user.full_name,
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_active_user)):
    return current_user


@router.post("/change-password")
async def change_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    if not verify_password(payload.old_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password does not match",
        )

    current_user.hashed_password = get_password_hash(payload.new_password)
    db.add(current_user)
    await db.commit()
    return {"message": "Password updated successfully"}


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_active_user)):
    return {"message": "Logged out successfully"}


@router.post("/seed")
async def trigger_seed(db: AsyncSession = Depends(get_db)):
    result = await seed_database(db)
    return {
        "status": "success",
        "data": result,
    }
