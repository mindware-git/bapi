from fastapi import Depends, APIRouter, HTTPException, Query, File, UploadFile, Form
from sqlmodel import Session, select
from uuid import UUID, uuid4
import os
from typing import List

from ..models import (
    Profile,
    Post,
    PostPublic,
    PostCreate,
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
    os.makedirs(uploads_dir, exist_ok=True)
    os.makedirs(f"{uploads_dir}/images", exist_ok=True)
    os.makedirs(f"{uploads_dir}/videos", exist_ok=True)

    # Save files and get their URLs
    media_urls = []
    for file in files:
        # Generate unique filename
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid4()}{file_extension}"

        # Determine file type and save accordingly
        if file.content_type and file.content_type.startswith("image/"):
            file_path = f"{uploads_dir}/images/{unique_filename}"
        elif file.content_type and file.content_type.startswith("video/"):
            file_path = f"{uploads_dir}/videos/{unique_filename}"
        else:
            # Skip unsupported file types
            continue

        # Save file
        with open(file_path, "wb") as buffer:
            content = file.file.read()
            buffer.write(content)

        # Add URL to media_urls
        media_urls.append(f"/{file_path}")

    # Create post using PostCreate model for consistency
    post_create = PostCreate(
        text=text, profile_id=UUID(profile_id), media_urls=media_urls
    )

    db_post = Post.model_validate(post_create)
    session.add(db_post)
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
