from collections.abc import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from services.api.auth.security import decode_token
from services.api.database import get_db
from services.api.models.user import User, UserRole

security_scheme = HTTPBearer(auto_error=False)


class TenantContext(BaseModel):
    user_id: str
    workspace_id: str
    role: UserRole
    email: str
    full_name: str


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error_code": "AUTH_REQUIRED", "message": "Authentication token missing"},
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = decode_token(credentials.credentials)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error_code": "INVALID_TOKEN", "message": "Token is invalid or expired"},
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload["sub"]
    result = await db.execute(select(User).where(User.id == user_id, User.is_active == True))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error_code": "USER_NOT_FOUND", "message": "User inactive or does not exist"},
        )
    return user


async def get_tenant_context(
    current_user: User = Depends(get_current_user),
) -> TenantContext:
    return TenantContext(
        user_id=current_user.id,
        workspace_id=current_user.workspace_id,
        role=current_user.role,
        email=current_user.email,
        full_name=current_user.full_name,
    )


def require_role(allowed_roles: list[UserRole]) -> Callable:
    def role_checker(tenant: TenantContext = Depends(get_tenant_context)) -> TenantContext:
        if tenant.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"error_code": "FORBIDDEN", "message": "Insufficient permissions for this action"},
            )
        return tenant
    return role_checker
