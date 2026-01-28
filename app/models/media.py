from sqlmodel import Field, Session, SQLModel, select
from sqlalchemy import Column, JSON
import uuid
from datetime import datetime, timezone


class MediaBase(SQLModel):
    original_url: str
    thumbnail_url: str | None = None
    media_type: str  # "image", "video"
    file_size: int | None = None  # bytes
    width: int | None = None
    height: int | None = None
    filename: str  # 원본 파일명
    content_type: str | None = None  # MIME 타입
    object_type: str  # "post", "comment", "message"
    object_id: uuid.UUID
    duration: int | None = None  # 비디오 길이 (초)
    video_codec: str | None = None  # 비디오 코덱


class Media(MediaBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    object_type: str  # "post", "comment", "message"
    object_id: uuid.UUID
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class MediaCreate(MediaBase):
    pass


class MediaPublic(MediaBase):
    id: uuid.UUID
    created_at: datetime
