from fastapi import (
    Depends,
    APIRouter,
    HTTPException,
    Query,
    WebSocket,
    WebSocketDisconnect,
)
from sqlmodel import Session, select
from uuid import UUID
import os
import uuid as uuid_lib
from typing import List, Dict

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
from ..database import get_session, engine


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


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[UUID, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, chat_id: UUID):
        await websocket.accept()
        if chat_id not in self.active_connections:
            self.active_connections[chat_id] = []
        self.active_connections[chat_id].append(websocket)

    def disconnect(self, websocket: WebSocket, chat_id: UUID):
        if (
            chat_id in self.active_connections
            and websocket in self.active_connections[chat_id]
        ):
            self.active_connections[chat_id].remove(websocket)
            if not self.active_connections[chat_id]:
                del self.active_connections[chat_id]

    async def broadcast(self, message: str, chat_id: UUID):
        if chat_id in self.active_connections:
            connections = self.active_connections[chat_id]
            for connection in connections:
                await connection.send_text(message)


manager = ConnectionManager()


@router.websocket("/ws/{chat_id}")
async def websocket_endpoint(websocket: WebSocket, chat_id: UUID):
    await manager.connect(websocket, chat_id)
    try:
        while True:
            data = await websocket.receive_json()
            # Expected: {"profile_id": "...", "text": "...", "media_file_ids": []}
            with Session(engine) as session:
                profile_id_str = data.get("profile_id")
                if not profile_id_str:
                    continue  # Ignore malformed data

                # TODO: Add validation that profile exists and is in this chat

                db_message = Message(
                    text=data.get("text", ""),
                    chat_id=chat_id,
                    profile_id=UUID(profile_id_str),
                    media_file_ids=data.get("media_file_ids", []),
                )
                session.add(db_message)
                session.commit()
                session.refresh(db_message)

                message_to_broadcast = MessagePublic.model_validate(db_message)

            await manager.broadcast(
                message_to_broadcast.model_dump_json(), chat_id=chat_id
            )

    except WebSocketDisconnect:
        manager.disconnect(websocket, chat_id)
        await manager.broadcast(f"A client has left the chat", chat_id=chat_id)
    except Exception as e:
        print(f"Error in websocket: {e}")
        manager.disconnect(websocket, chat_id)
