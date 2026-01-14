from sqlmodel import Field, SQLModel, Relationship
from sqlalchemy import Column, JSON
import uuid
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.profile import Profile

from app.models.profile import ProfileChatLink


class ChatBase(SQLModel):
    name: str | None = None


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
    media_file_ids: list[uuid.UUID] = Field(
        default_factory=list, sa_column=Column(JSON)
    )


class MessageCreate(MessageBase):
    chat_id: uuid.UUID
    profile_id: uuid.UUID


class MessagePublic(MessageBase):
    id: uuid.UUID
