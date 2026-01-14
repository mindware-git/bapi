from sqlmodel import Field, SQLModel, Relationship
from sqlalchemy import Column, JSON
import uuid
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.profile import Profile
    from app.models.post import Post


class CommentBase(SQLModel):
    text: str


class Comment(CommentBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    parent_id: uuid.UUID | None = Field(default=None, foreign_key="comment.id")

    post_id: uuid.UUID = Field(foreign_key="post.id")
    post: "Post" = Relationship(back_populates="comments")

    profile_id: uuid.UUID = Field(foreign_key="profile.id")
    profile: "Profile" = Relationship(back_populates="comments")

    media_file_ids: list[uuid.UUID] = Field(
        default_factory=list, sa_column=Column(JSON)
    )


class CommentCreate(CommentBase):
    post_id: uuid.UUID
    profile_id: uuid.UUID
    parent_id: uuid.UUID | None = None


class CommentPublic(CommentBase):
    id: uuid.UUID
    post_id: uuid.UUID
    profile_id: uuid.UUID
    parent_id: uuid.UUID | None = None
