from fastapi import Depends, APIRouter, HTTPException, File, UploadFile, Form
from sqlmodel import Session, select
from uuid import UUID, uuid4
import os
from typing import List

from ..models.media import (
    Media,
    MediaCreate,
    MediaPublic,
)
from ..database import get_session
from ..utils.media_utils import create_thumbnail, get_image_dimensions

router = APIRouter()


@router.post("/upload/images/", response_model=List[MediaPublic])
def upload_images(
    *,
    session: Session = Depends(get_session),
    files: List[UploadFile] = File(...),
    object_type: str = Form(...),
    object_id: str = Form(...),
):
    """
    범용 이미지 업로드 API
    - object_type: "post", "comment", "message" 등
    - object_id: 해당 객체의 UUID
    """
    # Validate object_id format
    try:
        object_uuid = UUID(object_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid object_id format")

    # Create uploads directory if it doesn't exist
    uploads_dir = "uploads"
    os.makedirs(f"{uploads_dir}/images/originals", exist_ok=True)
    os.makedirs(f"{uploads_dir}/images/thumbnails", exist_ok=True)

    uploaded_media = []

    for file in files:
        # Validate file type
        if not file.content_type or not file.content_type.startswith("image/"):
            continue  # Skip non-image files

        # Generate unique filename
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid4()}{file_extension}"

        # Save original file
        original_path = f"{uploads_dir}/images/originals/{unique_filename}"
        with open(original_path, "wb") as buffer:
            content = file.file.read()
            buffer.write(content)

        # Get file size
        file_size = os.path.getsize(original_path)

        # Get image dimensions and create thumbnail
        width, height = get_image_dimensions(original_path)

        # Create thumbnail
        thumbnail_filename = f"{uuid4()}.jpg"
        thumbnail_path = f"{uploads_dir}/images/thumbnails/{thumbnail_filename}"
        created_thumbnail_path = create_thumbnail(original_path, thumbnail_path)
        thumbnail_url = f"/uploads/images/thumbnails/{thumbnail_filename}"

        # Create media record
        media_create = MediaCreate(
            original_url=f"/uploads/images/originals/{unique_filename}",
            thumbnail_url=thumbnail_url,
            media_type="image",
            file_size=file_size,
            width=width,
            height=height,
            filename=file.filename or unique_filename,
            content_type=file.content_type,
            object_type=object_type,
            object_id=object_uuid,
        )

        db_media = Media.model_validate(media_create)
        session.add(db_media)
        session.commit()
        session.refresh(db_media)

        uploaded_media.append(db_media)

    return uploaded_media


@router.get("/media/{media_id}", response_model=MediaPublic)
def get_media(
    *,
    session: Session = Depends(get_session),
    media_id: UUID,
):
    """미디어 파일 정보 조회"""
    media = session.get(Media, media_id)
    if not media:
        raise HTTPException(status_code=404, detail="Media not found")
    return media


@router.get("/media/", response_model=List[MediaPublic])
def list_media(
    *,
    session: Session = Depends(get_session),
    object_type: str | None = None,
    object_id: UUID | None = None,
    offset: int = 0,
    limit: int = 100,
):
    """미디어 파일 목록 조회"""
    query = select(Media)

    if object_type:
        query = query.where(Media.object_type == object_type)

    if object_id:
        query = query.where(Media.object_id == object_id)

    media_list = session.exec(query.offset(offset).limit(limit)).all()
    return media_list
