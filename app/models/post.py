from sqlmodel import Field, SQLModel, Relationship
from sqlalchemy import Column, JSON
import uuid
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.profile import Profile


class PostBase(SQLModel):
    text: str | None = None


class Post(PostBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    profile_id: uuid.UUID = Field(foreign_key="profile.id")
    profile: "Profile" = Relationship(back_populates="posts")
    comments: list["Comment"] = Relationship(back_populates="post")
    media_file_ids: list[uuid.UUID] = Field(
        default_factory=list, sa_column=Column(JSON)
    )


class PostCreate(PostBase):
    profile_id: uuid.UUID


class PostPublic(PostBase):
    id: uuid.UUID
    profile_id: uuid.UUID


class Comment(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    parent_id: uuid.UUID | None = Field(default=None, foreign_key="comment.id")
    text: str
    post_id: uuid.UUID = Field(foreign_key="post.id")
    post: "Post" = Relationship(back_populates="comments")
    profile_id: uuid.UUID = Field(foreign_key="profile.id")
    profile: "Profile" = Relationship(back_populates="comments")
    media_file_ids: list[uuid.UUID] = Field(
        default_factory=list, sa_column=Column(JSON)
    )
