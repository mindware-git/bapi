from sqlmodel import SQLModel
from typing import Optional


class TokenResponse(SQLModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class GoogleCallbackRequest(SQLModel):
    code: str
    state: Optional[str] = None


class RefreshTokenRequest(SQLModel):
    refresh_token: str


class UserInfo(SQLModel):
    id: str
    email: str
    name: Optional[str] = None
    picture: Optional[str] = None
