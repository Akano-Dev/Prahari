"""Authentication routes — register, login (JWT), and current-user."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from ..core.config import Settings, get_settings
from ..core.deps import Container, get_container, get_current_user
from ..core.security import create_access_token, hash_password, verify_password
from ..domain.models import User
from ..schemas.api import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UpdateProfileRequest,
    UserResponse,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def _to_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id, email=user.email, display_name=user.display_name,
        avatar=user.avatar,
        created_at=user.created_at.isoformat() if user.created_at else None,
    )


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(req: RegisterRequest, container: Container = Depends(get_container)):
    if await container.repo.users.get_by_email(req.email):
        raise HTTPException(status.HTTP_409_CONFLICT, "email already registered")
    user = User(email=req.email, password_hash=hash_password(req.password),
                display_name=req.display_name)
    await container.repo.users.add(user)
    return _to_response(user)


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, container: Container = Depends(get_container),
                settings: Settings = Depends(get_settings)):
    user = await container.repo.users.get_by_email(req.email)
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid credentials")
    token = create_access_token(user.id, settings.jwt_secret, settings.jwt_expires_seconds,
                                email=user.email)
    return TokenResponse(access_token=token, expires_in=settings.jwt_expires_seconds)


@router.get("/me", response_model=UserResponse)
async def me(user: User = Depends(get_current_user)):
    return _to_response(user)


@router.patch("/me", response_model=UserResponse)
async def update_me(
    req: UpdateProfileRequest,
    user: User = Depends(get_current_user),
    container: Container = Depends(get_container),
):
    if req.display_name is not None:
        user.display_name = req.display_name
    if req.avatar is not None:
        user.avatar = req.avatar or None      # "" clears the picture
    await container.repo.users.update(user)
    return _to_response(user)
