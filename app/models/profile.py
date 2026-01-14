from sqlmodel import Field, Session, SQLModel, Relationship, select
from sqlalchemy import Column, JSON
import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.chat import Chat, Message
    from app.models.post import Post, Comment


# 연결 테이블 정의
class ProfileChatLink(SQLModel, table=True):
    profile_id: uuid.UUID = Field(foreign_key="profile.id", primary_key=True)
    chat_id: uuid.UUID = Field(foreign_key="chat.id", primary_key=True)


class ProfileBase(SQLModel):
    name: str = Field(unique=True)
    bio: str | None = None
    avatar: str | None = None
    posts_count: int = 0
    followers_count: int = 0
    following_count: int = 0


class Profile(ProfileBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    chats: list["Chat"] = Relationship(
        back_populates="profiles", link_model=ProfileChatLink
    )

    messages: list["Message"] = Relationship(back_populates="profile")
    posts: list["Post"] = Relationship(back_populates="profile")
    comments: list["Comment"] = Relationship(back_populates="profile")


class ProfileCreate(ProfileBase):
    pass


class ProfilePublic(ProfileBase):
    id: uuid.UUID


class ProfileUpdate(SQLModel):
    name: str | None = None
