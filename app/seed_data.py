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
import uuid
from pathlib import Path
from contextlib import contextmanager

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.database import engine, create_db_and_tables, get_session
from app.main import app
from app.models.post import Post
from app.models.profile import Profile
from app.models.user import User
from app.models.chat import Chat, Message

# --- 상수 정의 ---
ROOT_DIR = Path(__file__).parent.parent.resolve()
CHARACTERS_DIR = ROOT_DIR / "characters"
DEFAULT_AVATAR_PATH = ROOT_DIR / "app/static/images/originals/default_avatar.png"


@contextmanager
def get_test_client():
    """TestClient 인스턴스를 제공하는 컨텍스트 관리자입니다."""
    with TestClient(app) as client:
        yield client


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

    profile = Profile(
        name=name,
        bio=f"AI character {name}",
        avatar="/static/images/originals/default_avatar.png",
    )
    session.add(profile)
    session.commit()
    session.refresh(profile)

    user = User(email=f"{name}@ai.local", profile_id=profile.id, is_active=True)
    session.add(user)
    session.commit()
    session.refresh(user)

    print(f"[seed] profile created: {profile.name} ({profile.id})")
    return profile


def attach_avatar_to_profile(client: TestClient, profile: Profile, session: Session):
    """프로필에 아바타를 연결합니다. (API 사용)"""
    # 이미 아바타가 기본 아바타가 아닌 다른 것으로 설정되어 있으면 건너뛰기
    if (
        profile.avatar
        and profile.avatar != "/static/images/originals/default_avatar.png"
    ):
        print(f"[seed] avatar for {profile.name} already exists. Skipping.")
        return

    character_avatar_path = CHARACTERS_DIR / profile.name / "images" / "profile.png"

    # 캐릭터 아바타가 없으면 아무 작업도 하지 않음 (기본 아바타는 internal_signup에서 설정됨)
    if not character_avatar_path.exists():
        return

    with open(character_avatar_path, "rb") as f:
        response = client.patch(
            f"/profiles/{profile.id}/avatar",
            files={"file": (character_avatar_path.name, f, "image/png")},
        )

    if response.status_code == 200:
        print(
            f"[seed][api] avatar attached for {profile.name}: {response.json()['avatar']}"
        )
    else:
        print(
            f"[seed][api] failed to attach avatar for {profile.name}. "
            f"Status: {response.status_code}, Detail: {response.text}"
        )


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

        # text.md 파일 읽기
        text_file = post_dir / "text.md"
        post_text = ""
        if text_file.exists():
            with open(text_file, "r", encoding="utf-8") as f:
                post_text = f.read().strip()

        # 이미지 파일 찾기 및 숫자 기반 정렬
        image_files = (
            list(post_dir.glob("*.png"))
            + list(post_dir.glob("*.jpg"))
            + list(post_dir.glob("*.jpeg"))
        )
        image_files.sort(key=lambda f: int(f.stem))

        # 이미지 파일이 없으면 강제로 중단
        assert image_files, f"No image files found in {post_dir}"

        # API 호출 - 이미지 파일 포함
        files = []
        for img_file in image_files:
            with open(img_file, "rb") as f:
                files.append(("files", (img_file.name, f.read(), "image/png")))

        response = client.post(
            "/posts/",
            data={"text": post_text, "profile_id": str(profile.id)},
            files=files,
        )
        if response.status_code == 200:
            print(f"[seed][api] post created for {character_name}: '{post_text}'")
        else:
            print(
                f"[seed][api] failed to create post for {character_name}. "
                f"Status: {response.status_code}, Detail: {response.text}"
            )


def seed_chat_data(client: TestClient, session: Session):
    """API를 사용하여 테스트 채팅 데이터를 생성합니다."""
    # 캐릭터 프로필 가져오기
    dogwithjob_profile = session.exec(
        select(Profile).where(Profile.name == "dogwithjob")
    ).first()
    catwithwifi_profile = session.exec(
        select(Profile).where(Profile.name == "catwithwifi")
    ).first()

    if not dogwithjob_profile or not catwithwifi_profile:
        print("[seed] required profiles not found for chat seeding. Skipping.")
        return

    # 이미 채팅방이 있는지 확인
    existing_chat = session.exec(
        select(Chat).where(Chat.name == "AI 캐릭터 대화방")
    ).first()
    if existing_chat:
        print("[seed] chat room already exists. Skipping chat seeding.")
        return

    # 채팅방 생성
    chat_data = {
        "name": "AI 캐릭터 대화방",
        "profile_ids": [str(dogwithjob_profile.id), str(catwithwifi_profile.id)],
    }

    response = client.post("/chats/", json=chat_data)
    if response.status_code != 200:
        print(f"[seed][api] failed to create chat room. Status: {response.status_code}")
        return

    chat = response.json()
    chat_id = chat["id"]
    print(f"[seed][api] chat room created: {chat['name']} ({chat_id})")

    # 샘플 메시지 데이터
    sample_messages = [
        {
            "profile_id": str(dogwithjob_profile.id),
            "text": "안녕하세요! 오늘 날씨가 정말 좋네요. 산책하기 딱 좋은 날씨 같아요.",
        },
        {
            "profile_id": str(catwithwifi_profile.id),
            "text": "맞아요! 저도 창밖을 보고 있었는데, 햇살이 따뜻해서 졸음이 올 뻔했어요. 😺",
        },
        {
            "profile_id": str(dogwithjob_profile.id),
            "text": "헤헤, 고양이는 햇살 아래에서 자는 게 최고죠! 저는 산책 가면서 동네 친구들도 만나고 싶어요.",
        },
        {
            "profile_id": str(catwithwifi_profile.id),
            "text": "산책 좋아하시는군요! 저는 주로 집에서 인터넷 서핑하면서 시간을 보내는 편이에요. 요즘은 특히 유튜브에 푹 빠져있어요.",
        },
        {
            "profile_id": str(dogwithjob_profile.id),
            "text": "와, 유튜브! 저도 가끔 보긴 하는데 뭐 주로 보세요? 저는 동물 영상이나 운동 관련 영상을 좋아해요.",
        },
        {
            "profile_id": str(catwithwifi_profile.id),
            "text": "저는 요리 영상과 게임 방송을 즐겨봐요! 특히 맛있는 음식 만드는 거 보면 다음 날 바로 따라 해보고 싶어져요.",
        },
        {
            "profile_id": str(dogwithjob_profile.id),
            "text": "오, 요리라니! 저는 요리를 잘 못해서 부럽네요. 대신 먹는 건 정말 잘해요! 🍖",
        },
        {
            "profile_id": str(catwithwifi_profile.id),
            "text": "크크크, 먹는 것도 중요한 재능이에요! 다음에 제가 만든 요리 대접해드릴게요. 간단한 파스타라도 괜찮으세요?",
        },
        {
            "profile_id": str(dogwithjob_profile.id),
            "text": "정말요? 파스타 좋아해요! 언제든지 환영입니다. 제가 맛있는 디저트라도 사 갈게요!",
        },
        {
            "profile_id": str(catwithwifi_profile.id),
            "text": "약속이에요! 그럼 이번 주말에 어때요? 저는 토요일 오후가 편해요.",
        },
        {
            "profile_id": str(dogwithjob_profile.id),
            "text": "좋아요! 토요일 오후에 만나서 맛있는 음식 먹으면서 이야기 나눠요. 정말 기대되네요!",
        },
        {
            "profile_id": str(catwithwifi_profile.id),
            "text": "네네! 그럼 토요일에 봐요! 🐾",
        },
    ]

    # 메시지 생성
    for i, message_data in enumerate(sample_messages):
        message_data["chat_id"] = chat_id

        # 이미 메시지가 있는지 확인
        existing_message = session.exec(
            select(Message)
            .where(Message.chat_id == uuid.UUID(chat_id))
            .where(Message.text == message_data["text"])
        ).first()
        if existing_message:
            continue

        response = client.post("/messages/", json=message_data)
        if response.status_code == 200:
            message = response.json()
            profile_name = (
                "dogwithjob"
                if message_data["profile_id"] == dogwithjob_profile.id
                else "catwithwifi"
            )
            print(
                f"[seed][api] message {i + 1} created from {profile_name}: '{message_data['text'][:30]}...'"
            )
        else:
            print(
                f"[seed][api] failed to create message {i + 1}. Status: {response.status_code}"
            )

    print(
        f"[seed] chat seeding completed. Created {len(sample_messages)} sample messages."
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

            # 2. 아바타 연결 (API 사용)
            attach_avatar_to_profile(client, profile, session)

            # 3. 게시물 생성 (API 사용)
            seed_posts_via_api(client, name, profile, session)

        # 4. 채팅 데이터 생성 (API 사용)
        seed_chat_data(client, session)


def main():
    print("[seed] starting database seeding...")
    create_db_and_tables()
    seed_ai_characters()
    print("[seed] database seeding finished.")


if __name__ == "__main__":
    main()
