from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from uuid import UUID

from ..database import get_session
from ..models.comment import Comment, CommentCreate, CommentPublic
from ..models.post import Post
from ..models.profile import Profile

router = APIRouter(
    prefix="/comments",
    tags=["comments"],
)


@router.post("/", response_model=CommentPublic)
def create_comment(
    *,
    session: Session = Depends(get_session),
    comment: CommentCreate,
):
    # Validate post
    post = session.get(Post, comment.post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    # Validate profile
    profile = session.get(Profile, comment.profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    # Validate parent comment if exists
    if comment.parent_id:
        parent_comment = session.get(Comment, comment.parent_id)
        if not parent_comment:
            raise HTTPException(status_code=404, detail="Parent comment not found")
        # Ensure the parent comment belongs to the same post
        if parent_comment.post_id != comment.post_id:
            raise HTTPException(
                status_code=400,
                detail="Parent comment does not belong to the same post",
            )

    db_comment = Comment.model_validate(comment)
    session.add(db_comment)
    session.commit()
    session.refresh(db_comment)
    return db_comment


@router.get("/{comment_id}", response_model=CommentPublic)
def read_comment(
    *,
    session: Session = Depends(get_session),
    comment_id: UUID,
):
    comment = session.get(Comment, comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    return comment


@router.get("/post/{post_id}", response_model=list[CommentPublic])
def read_comments_for_post(
    *,
    session: Session = Depends(get_session),
    post_id: UUID,
    offset: int = 0,
    limit: int = Query(default=100, le=100),
):
    post = session.get(Post, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    comments = session.exec(
        select(Comment).where(Comment.post_id == post_id).offset(offset).limit(limit)
    ).all()
    return comments


@router.delete("/{comment_id}")
def delete_comment(
    *,
    session: Session = Depends(get_session),
    comment_id: UUID,
    # TODO: Add authentication to get current user
    # current_user: Profile = Depends(get_current_user),
):
    comment = session.get(Comment, comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    # if comment.profile_id != current_user.id:
    #     raise HTTPException(status_code=403, detail="Not authorized to delete this comment")

    session.delete(comment)
    session.commit()
    return {"ok": True}
