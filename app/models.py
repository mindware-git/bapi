from sqlmodel import Field, Session, SQLModel, Relationship, select
from sqlalchemy import Column, JSON
import uuid
from datetime import datetime, timezone


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


# data model
class ChatBase(SQLModel):
    name: str | None = None


# table model
class Chat(ChatBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    profiles: list["Profile"] = Relationship(
        back_populates="chats", link_model=ProfileChatLink
    )
    messages: list["Message"] = Relationship(back_populates="chat")


class ChatPublic(ChatBase):
    id: uuid.UUID


class ChatCreate(ChatBase):
    profile_ids: list[uuid.UUID]


class MessageBase(SQLModel):
    text: str


class Message(MessageBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    chat_id: uuid.UUID = Field(foreign_key="chat.id")
    chat: "Chat" = Relationship(back_populates="messages")

    profile_id: uuid.UUID = Field(foreign_key="profile.id")
    profile: "Profile" = Relationship(back_populates="messages")


class MessageCreate(MessageBase):
    chat_id: uuid.UUID
    profile_id: uuid.UUID


class MessagePublic(MessageBase):
    id: uuid.UUID


class PostBase(SQLModel):
    text: str | None = None
    media_urls: list[str] = Field(sa_column=Column(JSON))


class Post(PostBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    profile_id: uuid.UUID = Field(foreign_key="profile.id")
    profile: "Profile" = Relationship(back_populates="posts")

    comments: list["Comment"] = Relationship(back_populates="post")


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


# class PostPublicWithComments(PostPublic):
#     comments: list[CommentPublic] = []
