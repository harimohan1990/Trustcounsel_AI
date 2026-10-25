import re

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from services.api.auth.dependencies import (
    TenantContext,
    get_current_user,
    get_tenant_context,
)
from services.api.auth.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from services.api.database import get_db
from services.api.models.audit import AuditEvent
from services.api.models.user import User, UserRole
from services.api.models.workspace import Workspace

router = APIRouter(prefix="/auth", tags=["Authentication"])


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str
    workspace_name: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    workspace_id: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    # Check email duplicate
    existing = await db.execute(select(User).where(User.email == req.email.lower()))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error_code": "EMAIL_EXISTS", "message": "Email is already registered"},
        )

    # Create workspace
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", req.workspace_name.lower()).strip("-") or "default-workspace"
    workspace = Workspace(name=req.workspace_name, slug=f"{slug}-{int(re.sub(r'[^0-9]', '', str(hash(req.email))[:6]))}")
    db.add(workspace)
    await db.flush()

    # Create User
    user = User(
        workspace_id=workspace.id,
        email=req.email.lower(),
        password_hash=hash_password(req.password),
        full_name=req.full_name,
        role=UserRole.ADMINISTRATOR,  # First user in workspace is admin
    )
    db.add(user)
    await db.flush()

    # Audit log
    audit = AuditEvent(
        workspace_id=workspace.id,
        user_id=user.id,
        action="USER_REGISTERED",
        entity_type="user",
        entity_id=user.id,
        details=f'{{"email": "{user.email}", "role": "{user.role.value}"}}',
    )
    db.add(audit)
    await db.commit()

    token = create_access_token({"sub": user.id, "workspace_id": workspace.id, "role": user.role.value})
    return AuthResponse(
        access_token=token,
        user=UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=user.role.value,
            workspace_id=workspace.id,
        ),
    )


@router.post("/login", response_model=AuthResponse)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == req.email.lower(), User.is_active == True))
    user = result.scalar_one_or_none()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error_code": "INVALID_CREDENTIALS", "message": "Invalid email or password"},
        )

    token = create_access_token({"sub": user.id, "workspace_id": user.workspace_id, "role": user.role.value})
    return AuthResponse(
        access_token=token,
        user=UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=user.role.value,
            workspace_id=user.workspace_id,
        ),
    )


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    return {"success": True, "message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
async def me(tenant: TenantContext = Depends(get_tenant_context)):
    return UserResponse(
        id=tenant.user_id,
        email=tenant.email,
        full_name=tenant.full_name,
        role=tenant.role.value,
        workspace_id=tenant.workspace_id,
    )
