from fastapi import Depends, APIRouter, HTTPException, Query, File, UploadFile, Form
from sqlmodel import Session, select
from uuid import UUID, uuid4
import os
from typing import List

from ..models.profile import Profile
from ..models.post import (
    Post,
    PostPublic,
    PostCreate,
)
from ..models.media import (
    Media,
    MediaCreate,
)
from ..database import get_session

router = APIRouter()


@router.post("/posts/", response_model=PostPublic)
def create_post(
    *,
    session: Session = Depends(get_session),
    text: str = Form(...),
    profile_id: str = Form(...),
    files: List[UploadFile] = File(default=[]),
):
    # Validate that the profile exists
    try:
        profile_uuid = UUID(profile_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid profile_id format")

    profile = session.get(Profile, profile_uuid)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    # Create uploads directory if it doesn't exist
    uploads_dir = "uploads"
    os.makedirs(f"{uploads_dir}/images/originals", exist_ok=True)
    os.makedirs(f"{uploads_dir}/images/thumbnails", exist_ok=True)
    os.makedirs(f"{uploads_dir}/videos/originals", exist_ok=True)
    os.makedirs(f"{uploads_dir}/videos/thumbnails", exist_ok=True)

    # Create post first
    post_create = PostCreate(text=text, profile_id=UUID(profile_id))
    db_post = Post.model_validate(post_create)
    session.add(db_post)
    session.commit()
    session.refresh(db_post)

    # Process and save files
    media_file_ids = []
    for file in files:
        # Generate unique filename
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid4()}{file_extension}"

        # Determine file type and save accordingly
        if file.content_type and file.content_type.startswith("image/"):
            original_path = f"{uploads_dir}/images/originals/{unique_filename}"
            media_type = "image"
        elif file.content_type and file.content_type.startswith("video/"):
            original_path = f"{uploads_dir}/videos/originals/{unique_filename}"
            media_type = "video"
        else:
            # Skip unsupported file types
            continue

        # Save original file
        with open(original_path, "wb") as buffer:
            content = file.file.read()
            buffer.write(content)

        # Get file size
        file_size = os.path.getsize(original_path)

        # Create media record with new structure
        media_create = MediaCreate(
            original_url=f"/uploads/{media_type}s/originals/{unique_filename}",
            thumbnail_url=None,  # Will be generated later
            media_type=media_type,
            file_size=file_size,
            width=None,  # Will be extracted later
            height=None,  # Will be extracted later
            filename=file.filename or unique_filename,
            content_type=file.content_type,
            object_type="post",  # New field
            object_id=db_post.id,  # New field
        )
        db_media = Media.model_validate(media_create)
        session.add(db_media)
        session.commit()
        session.refresh(db_media)

        # Add media ID to post (as string)
        media_file_ids.append(str(db_media.id))

    # Update post with media file IDs (as strings)
    db_post.media_file_ids = media_file_ids
    session.commit()
    session.refresh(db_post)

    return db_post


@router.get("/posts/", response_model=list[PostPublic])
def read_posts(
    *,
    session: Session = Depends(get_session),
    offset: int = 0,
    limit: int = Query(default=100, le=100),
):
    posts = session.exec(select(Post).offset(offset).limit(limit)).all()
    return posts


@router.get("/posts/{post_id}", response_model=PostPublic)
def read_post(*, session: Session = Depends(get_session), post_id: UUID):
    post = session.get(Post, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post
