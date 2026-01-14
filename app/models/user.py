from sqlmodel import Field, Session, SQLModel, Relationship, select
import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.profile import ProfilePublic


class UserBase(SQLModel):
    email: str = Field(unique=True, index=True)
    is_active: bool = True
    is_superuser: bool = False


class User(UserBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    profile_id: uuid.UUID = Field(foreign_key="profile.id", unique=True)
    oauth_accounts: list["OAuthAccount"] = Relationship(back_populates="user")
    refresh_tokens: list["RefreshToken"] = Relationship(back_populates="user")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class UserCreate(SQLModel):
    email: str
    profile_id: uuid.UUID


class UserPublic(SQLModel):
    id: uuid.UUID
    email: str
    is_active: bool
    profile: "ProfilePublic"


class UserUpdate(SQLModel):
    email: str | None = None
    is_active: bool | None = None


class OAuthAccountBase(SQLModel):
    oauth_provider: str  # "google", "github", "kakao" 등
    provider_user_id: str  # 구글에서 제공하는 사용자 ID
    access_token: str | None = None
    refresh_token: str | None = None
    token_type: str | None = None
    expires_at: datetime | None = None
    scope: str | None = None


class OAuthAccount(OAuthAccountBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id")
    user: User = Relationship(back_populates="oauth_accounts")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class OAuthAccountCreate(OAuthAccountBase):
    user_id: uuid.UUID


class RefreshTokenBase(SQLModel):
    token: str = Field(unique=True, index=True)
    expires_at: datetime


class RefreshToken(RefreshTokenBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id")
    user: User = Relationship(back_populates="refresh_tokens")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_revoked: bool = False
