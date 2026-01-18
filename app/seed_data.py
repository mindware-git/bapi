"""
seed_data.py

- `characters` 디렉토리를 자동으로 스캔하여 AI 캐릭터를 시드합니다.
- 각 캐릭터에 대한 사용자 및 프로필을 생성합니다.
- 아바타 이미지를 처리하고 연결합니다. (API가 없으므로 DB 직접 조작)
  - `characters/{name}/images/profile.png` 가 있으면 사용합니다.
  - 없으면 `app/static/images/originals/default_avatar.png` 를 기본값으로 사용합니다.
- `TestClient`를 사용하여 `POST /posts/` API를 호출해 게시물을 생성합니다.
"""

import os
import shutil
import uuid
from pathlib import Path
from contextlib import contextmanager

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.database import engine, create_db_and_tables, get_session
from app.main import app
from app.models.media import Media
from app.models.post import Post
from app.models.profile import Profile
from app.models.user import User
from app.utils.media_utils import create_thumbnail, get_image_dimensions

# --- 상수 정의 ---
ROOT_DIR = Path(__file__).parent.parent.resolve()
CHARACTERS_DIR = ROOT_DIR / "characters"
UPLOADS_DIR = ROOT_DIR / "uploads"
DEFAULT_AVATAR_PATH = ROOT_DIR / "app/static/images/originals/default_avatar.png"


@contextmanager
def get_test_client():
    """TestClient 인스턴스를 제공하는 컨텍스트 관리자입니다."""
    with TestClient(app) as client:
        yield client


# --- 직접 DB/파일 조작 함수 (아바타용) ---
def create_avatar_media_directly(
    session: Session, profile_id: uuid.UUID, image_path: Path
) -> Media:
    """
    (API가 없으므로 직접 처리)
    주어진 이미지로부터 Media 객체를 생성, 파일을 복사하고 썸네일을 만듭니다.
    """
    media_id = uuid.uuid4()
    # 경로를 /uploads/ 로 시작하도록 수정
    media_dir_name = str(media_id)
    media_dir = UPLOADS_DIR / media_dir_name
    media_dir.mkdir(parents=True, exist_ok=True)

    original_filename = image_path.name
    original_dest_path = media_dir / original_filename
    shutil.copy2(image_path, original_dest_path)

    thumbnail_filename = f"thumbnail_{Path(original_filename).stem}.jpg"
    thumbnail_dest_path = media_dir / thumbnail_filename
    created_thumbnail_path = create_thumbnail(
        str(original_dest_path), str(thumbnail_dest_path)
    )

    width, height = get_image_dimensions(str(original_dest_path))
    media = Media(
        id=media_id,
        original_url=f"/uploads/{media_dir_name}/{original_filename}",
        thumbnail_url=f"/uploads/{media_dir_name}/{thumbnail_filename}",
        media_type="image",
        file_size=original_dest_path.stat().st_size,
        width=width,
        height=height,
        filename=original_filename,
        content_type=f"image/{image_path.suffix.strip('.')}",
        object_type="profile_avatar",
        object_id=profile_id,
    )
    session.add(media)
    session.commit()
    session.refresh(media)
    return media


# --- 시딩 로직 ---
def internal_signup(name: str, session: Session) -> Profile:
    """사용자 및 기본 프로필을 생성합니다 (기존 로직 유지)."""
    existing_user = session.exec(
        select(User).where(User.email == f"{name}@ai.local")
    ).first()
    if existing_user:
        profile = session.get(Profile, existing_user.profile_id)
        # 멱등성을 위해, 이미 생성된 경우에도 객체를 반환하여 후속 작업을 진행하게 함
        if profile:
            return profile

    profile = Profile(name=name, bio=f"AI character {name}")
    session.add(profile)
    session.commit()
    session.refresh(profile)

    user = User(email=f"{name}@ai.local", profile_id=profile.id, is_active=True)
    session.add(user)
    session.commit()
    session.refresh(user)

    print(f"[seed] profile created: {profile.name} ({profile.id})")
    return profile


def attach_avatar_to_profile(profile: Profile, session: Session):
    """프로필에 아바타를 연결합니다. (API가 없으므로 직접 DB 조작)"""
    character_avatar_path = CHARACTERS_DIR / profile.name / "images" / "profile.png"
    avatar_path = (
        character_avatar_path if character_avatar_path.exists() else DEFAULT_AVATAR_PATH
    )

    if avatar_path.exists():
        # 이미 아바타가 있는지 확인
        if (
            profile.avatar
            and profile.avatar != "/static/images/originals/default_avatar.png"
        ):
            return

        media = create_avatar_media_directly(session, profile.id, avatar_path)
        profile.avatar = media.original_url
        session.add(profile)
        session.commit()
        session.refresh(profile)
        print(f"[seed] avatar attached for {profile.name}: {media.original_url}")


def seed_posts_via_api(
    client: TestClient, character_name: str, profile: Profile, session: Session
):
    """`POST /posts/` API를 호출하여 캐릭터의 게시물을 시드합니다."""
    posts_dir = CHARACTERS_DIR / character_name / "posts"
    if not posts_dir.exists():
        return

    post_subdirs = [d for d in posts_dir.iterdir() if d.is_dir()]
    for post_dir in post_subdirs:
        post_text = f"A post from {character_name} (#{post_dir.name})"

        # API를 사용하기 전에 DB에서 먼저 확인하여 중복 API 호출 방지
        existing_post = session.exec(
            select(Post)
            .where(Post.profile_id == profile.id)
            .where(Post.text == post_text)
        ).first()
        if existing_post:
            continue

        # API 호출
        # 현재 게시물당 이미지를 연결하는 규칙이 없으므로 빈 파일로 호출
        response = client.post(
            "/posts/",
            data={"text": post_text, "profile_id": str(profile.id)},
            files={"files": []},
        )
        if response.status_code == 200:
            print(f"[seed][api] post created for {character_name}: '{post_text}'")
        else:
            print(
                f"[seed][api] failed to create post for {character_name}. "
                f"Status: {response.status_code}, Detail: {response.text}"
            )


def seed_ai_characters():
    """`characters` 디렉토리를 스캔하고 API를 사용하여 시드합니다."""
    if not CHARACTERS_DIR.exists():
        print(f"[seed] '{CHARACTERS_DIR}' not found. Skipping.")
        return

    character_names = [
        d.name
        for d in CHARACTERS_DIR.iterdir()
        if d.is_dir() and d.name != "__pycache__"
    ]

    with Session(engine) as session, get_test_client() as client:
        for name in character_names:
            # 1. 사용자/프로필 생성 (DB 직접)
            profile = internal_signup(name, session)

            # 2. 아바타 연결 (DB/파일 직접, 관련 API 없음)
            attach_avatar_to_profile(profile, session)

            # 3. 게시물 생성 (API 사용)
            seed_posts_via_api(client, name, profile, session)


def main():
    print("[seed] starting database seeding...")
    create_db_and_tables()
    seed_ai_characters()
    print("[seed] database seeding finished.")


if __name__ == "__main__":
    main()
