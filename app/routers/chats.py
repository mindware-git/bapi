from fastapi import Depends, APIRouter, HTTPException, Query, File, UploadFile, Form
from sqlmodel import Session, select
from uuid import UUID
import os
import uuid as uuid_lib
from typing import List

from ..models.profile import (
    Profile,
    ProfilePublic,
    ProfileCreate,
    ProfileUpdate,
    ProfileChatLink,
)
from ..models.post import (
    Post,
    PostPublic,
    PostCreate,
)
from ..models.chat import (
    Chat,
    ChatPublic,
    ChatCreate,
    Message,
    MessagePublic,
    MessageCreate,
)
from ..database import get_session


router = APIRouter()


@router.post("/chats/", response_model=ChatPublic)
def create_chat(*, session: Session = Depends(get_session), chat: ChatCreate):
    # Validate that at least one profile_id is provided
    if not chat.profile_ids or len(chat.profile_ids) == 0:
        raise HTTPException(
            status_code=400, detail="At least one profile_id is required"
        )

    # Validate that all profile_ids exist
    profiles = []
    for profile_id in chat.profile_ids:
        profile = session.get(Profile, profile_id)
        if not profile:
            raise HTTPException(
                status_code=404, detail=f"Profile with id {profile_id} not found"
            )
        profiles.append(profile)

    # Create the chat
    db_chat = Chat.model_validate(chat)
    session.add(db_chat)
    session.commit()
    session.refresh(db_chat)

    # Create ProfileChatLink entries
    for profile in profiles:
        link = ProfileChatLink(profile_id=profile.id, chat_id=db_chat.id)
        session.add(link)

    session.commit()

    return db_chat


@router.get("/chats/", response_model=list[ChatPublic])
def read_chats(
    *,
    session: Session = Depends(get_session),
    offset: int = 0,
    limit: int = Query(default=100, le=100),
):
    chats = session.exec(select(Chat).offset(offset).limit(limit)).all()
    return chats


@router.get("/chats/{chat_id}", response_model=ChatPublic)
def read_chat(*, session: Session = Depends(get_session), chat_id: UUID):
    chat = session.get(Chat, chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    return chat


@router.post("/messages/", response_model=MessagePublic)
def create_message(*, session: Session = Depends(get_session), message: MessageCreate):
    # Validate that the chat_id exists
    chat = session.get(Chat, message.chat_id)
    if not chat:
        raise HTTPException(
            status_code=404, detail=f"Chat with id {message.chat_id} not found"
        )

    # Validate that the profile_id exists (if provided)
    # For now, we'll assume profile_id is part of the message or associated with the chat
    # In a real implementation, you might want to validate the profile as well

    db_message = Message.model_validate(message)
    session.add(db_message)
    session.commit()
    session.refresh(db_message)
    return db_message


@router.get("/messages/", response_model=list[MessagePublic])
def read_messages(
    *,
    session: Session = Depends(get_session),
    offset: int = 0,
    limit: int = Query(default=100, le=100),
):
    messages = session.exec(select(Message).offset(offset).limit(limit)).all()
    return messages


@router.get("/chats/{chat_id}/messages/", response_model=list[MessagePublic])
def read_chat_messages(*, session: Session = Depends(get_session), chat_id: UUID):
    chat = session.get(Chat, chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    # Get messages for this chat
    messages = session.exec(select(Message).where(Message.chat_id == chat_id)).all()
    return messages
