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
from ..utils.media_utils import create_thumbnail, get_image_dimensions


def post_to_post_public(post: Post, session: Session) -> PostPublic:
    """Convert Post model to PostPublic with media URLs"""
    media_urls = []
    if post.media_file_ids:
        # Convert string IDs to UUID objects for query
        media_uuids = [UUID(media_id) for media_id in post.media_file_ids]
        media_records = session.exec(
            select(Media).where(Media.id.in_(media_uuids))
        ).all()
        media_urls = [media.original_url for media in media_records]

    return PostPublic(
        id=post.id, profile_id=post.profile_id, text=post.text, media_urls=media_urls
    )


router = APIRouter()


@router.post("/posts/", response_model=PostPublic)
def create_post(
    *,
    session: Session = Depends(get_session),
    text: str | None = Form(None),
    profile_id: str = Form(...),
    files: List[UploadFile] = File(...),
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

        # Extract metadata and create thumbnail for images
        thumbnail_url = None
        width = None
        height = None

        if media_type == "image":
            # Get image dimensions
            width, height = get_image_dimensions(original_path)

            # Create thumbnail
            thumbnail_filename = f"{uuid4()}.jpg"
            thumbnail_path = f"{uploads_dir}/images/thumbnails/{thumbnail_filename}"
            created_thumbnail_path = create_thumbnail(original_path, thumbnail_path)
            thumbnail_url = f"/uploads/images/thumbnails/{thumbnail_filename}"
        elif media_type == "video":
            # For videos, we'll set default dimensions for now
            # Video thumbnail generation can be added later with ffmpeg
            width, height = 1280, 720  # Default video dimensions
            thumbnail_url = None  # Will be implemented later

        # Create media record with complete metadata
        media_create = MediaCreate(
            original_url=f"/uploads/{media_type}s/originals/{unique_filename}",
            thumbnail_url=thumbnail_url,
            media_type=media_type,
            file_size=file_size,
            width=width,
            height=height,
            filename=file.filename or unique_filename,
            content_type=file.content_type,
            object_type="post",
            object_id=db_post.id,
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

    return post_to_post_public(db_post, session)


@router.get("/posts/", response_model=list[PostPublic])
def read_posts(
    *,
    session: Session = Depends(get_session),
    offset: int = 0,
    limit: int = Query(default=100, le=100),
):
    posts = session.exec(select(Post).offset(offset).limit(limit)).all()
    return [post_to_post_public(post, session) for post in posts]


@router.get("/posts/{post_id}", response_model=PostPublic)
def read_post(*, session: Session = Depends(get_session), post_id: UUID):
    post = session.get(Post, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post_to_post_public(post, session)
