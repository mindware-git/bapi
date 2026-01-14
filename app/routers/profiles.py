from fastapi import Depends, APIRouter, HTTPException, Query
from sqlmodel import Session, select
from uuid import UUID
from ..models.profile import (
    Profile,
    ProfilePublic,
    ProfileCreate,
    ProfileUpdate,
)
from ..models.post import (
    Post,
    PostPublic,
)
from ..database import get_session


router = APIRouter()


@router.post("/profiles/", response_model=ProfilePublic)
def create_profile(*, session: Session = Depends(get_session), profile: ProfileCreate):
    db_profile = Profile.model_validate(profile)
    session.add(db_profile)
    session.commit()
    session.refresh(db_profile)
    return db_profile


@router.get("/profiles/", response_model=list[ProfilePublic])
def read_profiles(
    *,
    session: Session = Depends(get_session),
    offset: int = 0,
    limit: int = Query(default=100, le=100),
):
    profiles = session.exec(select(Profile).offset(offset).limit(limit)).all()
    return profiles


@router.get("/profiles/{profile_id}", response_model=ProfilePublic)
def read_profile(*, session: Session = Depends(get_session), profile_id: UUID):
    profile = session.get(Profile, profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


@router.get("/users/{name}", response_model=ProfilePublic)
def read_user_by_name(*, session: Session = Depends(get_session), name: str):
    profile = session.exec(select(Profile).where(Profile.name == name)).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


@router.patch("/profiles/{profile_id}", response_model=ProfilePublic)
def update_profile(
    *, session: Session = Depends(get_session), profile_id: UUID, profile: ProfileUpdate
):
    db_profile = session.get(Profile, profile_id)
    if not db_profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    profile_data = profile.model_dump(exclude_unset=True)
    db_profile.sqlmodel_update(profile_data)
    session.add(db_profile)
    session.commit()
    session.refresh(db_profile)
    return db_profile


@router.delete("/profiles/{profile_id}")
def delete_profile(*, session: Session = Depends(get_session), profile_id: UUID):
    profile = session.get(Profile, profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    session.delete(profile)
    session.commit()
    return {"ok": True}


@router.get("/posts/", response_model=list[PostPublic])
def read_posts(
    *,
    session: Session = Depends(get_session),
    offset: int = 0,
    limit: int = Query(default=100, le=100),
):
    posts = session.exec(select(Post).offset(offset).limit(limit)).all()
    return posts


@router.get("/profiles/{profile_id}/posts/", response_model=list[PostPublic])
def read_profile_posts(*, session: Session = Depends(get_session), profile_id: UUID):
    profile: Profile = session.get(Profile, profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile.posts
