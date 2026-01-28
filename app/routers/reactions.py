from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from uuid import UUID
from ..database import get_session
from ..models.reaction import Reaction, ReactionCreate, ReactionPublic
from ..models.post import Post
from ..models.profile import Profile

router = APIRouter(
    prefix="/reactions",
    tags=["reactions"],
)


@router.post("/", response_model=ReactionPublic)
def toggle_reaction(
    *,
    session: Session = Depends(get_session),
    reaction: ReactionCreate,
):
    """좋아요 토글: 이미 있으면 삭제, 없으면 생성"""
    # Validate post
    post = session.get(Post, reaction.post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    # Validate profile
    profile = session.get(Profile, reaction.profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    # Validate reaction_type (currently only "like" is supported)
    if reaction.reaction_type != "like":
        raise HTTPException(
            status_code=400,
            detail=f"reaction_type '{reaction.reaction_type}' is not supported. Only 'like' is supported.",
        )

    # Check if reaction already exists
    existing_reaction = session.exec(
        select(Reaction).where(
            Reaction.post_id == reaction.post_id,
            Reaction.profile_id == reaction.profile_id,
            Reaction.reaction_type == reaction.reaction_type,
        )
    ).first()

    if existing_reaction:
        # Remove existing reaction (toggle off)
        session.delete(existing_reaction)
        session.commit()
        return existing_reaction
    else:
        # Create new reaction (toggle on)
        db_reaction = Reaction.model_validate(reaction)
        session.add(db_reaction)
        session.commit()
        session.refresh(db_reaction)
        return db_reaction


@router.get("/{reaction_id}", response_model=ReactionPublic)
def read_reaction(
    *,
    session: Session = Depends(get_session),
    reaction_id: UUID,
):
    """특정 좋아요 조회"""
    reaction = session.get(Reaction, reaction_id)
    if not reaction:
        raise HTTPException(status_code=404, detail="Reaction not found")
    return reaction


@router.get("/post/{post_id}", response_model=list[ReactionPublic])
def read_reactions_for_post(
    *,
    session: Session = Depends(get_session),
    post_id: UUID,
    offset: int = 0,
    limit: int = Query(default=100, le=100),
):
    """특정 게시물의 모든 좋아요 목록"""
    post = session.get(Post, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    reactions = session.exec(
        select(Reaction).where(Reaction.post_id == post_id).offset(offset).limit(limit)
    ).all()
    return reactions


@router.get("/post/{post_id}/profile/{profile_id}", response_model=ReactionPublic)
def check_reaction(
    *,
    session: Session = Depends(get_session),
    post_id: UUID,
    profile_id: UUID,
):
    """특정 유저가 특정 게시물에 좋아요를 눌렀는지 확인"""
    # Validate post
    post = session.get(Post, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    # Validate profile
    profile = session.get(Profile, profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    # Check if reaction exists
    reaction = session.exec(
        select(Reaction).where(
            Reaction.post_id == post_id,
            Reaction.profile_id == profile_id,
            Reaction.reaction_type == "like",
        )
    ).first()

    if not reaction:
        raise HTTPException(status_code=404, detail="Reaction not found")
    return reaction
