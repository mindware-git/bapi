import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine, select
from sqlmodel.pool import StaticPool
from ..main import app
from ..models import Profile, Chat, Message
from ..database import get_session


@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        # 테스트용 프로필 추가
        profile = Profile(name="TestUser", bio="Test Bio")
        session.add(profile)
        session.commit()
        session.refresh(profile)

        # 테스트용 채팅 추가
        chat = Chat(name="Test Chat")
        session.add(chat)
        session.commit()
        session.refresh(chat)

        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture(name="profiles")
def profiles_fixture(session: Session):
    # 테스트용 프로필 2개 추가
    profile_1 = Profile(name="TestUser1", bio="Test Bio 1")
    profile_2 = Profile(name="TestUser2", bio="Test Bio 2")
    session.add(profile_1)
    session.add(profile_2)
    session.commit()
    session.refresh(profile_1)
    session.refresh(profile_2)
    return [profile_1, profile_2]


@pytest.fixture(name="profile")
def profile_fixture(session: Session):
    profile = session.exec(select(Profile)).first()
    return profile


@pytest.fixture(name="chat_with_profiles")
def chat_with_profiles_fixture(session: Session, profiles: list):
    # 두 사용자가 참여하는 채팅 생성
    chat = Chat(name="Test Chat with Two Profiles")
    session.add(chat)
    session.commit()
    session.refresh(chat)

    # ProfileChatLink를 통해 프로필들과 채팅 연결
    from ..models import ProfileChatLink

    link_1 = ProfileChatLink(profile_id=profiles[0].id, chat_id=chat.id)
    link_2 = ProfileChatLink(profile_id=profiles[1].id, chat_id=chat.id)
    session.add(link_1)
    session.add(link_2)
    session.commit()

    return chat


def test_create_message(client: TestClient, chat_with_profiles: Chat, profile: Profile):
    # 채팅 ID와 프로필 ID로 메시지 생성
    message_data = {
        "text": "Test Message",
        "chat_id": str(chat_with_profiles.id),
        "profile_id": str(profile.id),
    }
    response = client.post("/messages/", json=message_data)
    data = response.json()

    assert response.status_code == 200
    assert data["text"] == message_data["text"]
    assert "id" in data


def test_create_message_invalid_chat_id(client: TestClient, profile: Profile):
    # 유효하지 않은 채팅 ID로 메시지 생성 시도
    message_data = {
        "text": "Test Message",
        "chat_id": "invalid-uuid",
        "profile_id": str(profile.id),
    }
    response = client.post("/messages/", json=message_data)
    assert response.status_code == 422


def test_create_message_missing_chat_id(client: TestClient, profile: Profile):
    # 채팅 ID가 없는 경우로 메시지 생성 시도
    message_data = {
        "text": "Test Message",
        "profile_id": str(profile.id),
    }
    response = client.post("/messages/", json=message_data)
    assert response.status_code == 422


def test_read_messages(client: TestClient, chat_with_profiles: Chat, profile: Profile):
    # 테스트용 메시지 생성
    message_text_1 = "First Message"
    message_text_2 = "Second Message"

    message_1 = Message(
        text=message_text_1, chat_id=chat_with_profiles.id, profile_id=profile.id
    )
    message_2 = Message(
        text=message_text_2, chat_id=chat_with_profiles.id, profile_id=profile.id
    )

    with client.app.dependency_overrides[get_session]() as session:
        session.add(message_1)
        session.add(message_2)
        session.commit()
        session.refresh(message_1)
        session.refresh(message_2)

    # 메시지 목록 조회
    response = client.get("/messages/")
    data = response.json()

    assert response.status_code == 200
    assert len(data) >= 2
    assert data[0]["text"] == message_text_1
    assert data[1]["text"] == message_text_2


def test_read_chat_messages(client: TestClient, session: Session, profile: Profile):
    # 테스트용 채팅 생성
    chat = Chat(name="Test Chat for Messages")
    session.add(chat)
    session.commit()
    session.refresh(chat)

    # 테스트용 메시지 생성
    message_text_1 = "Chat Message 1"
    message_text_2 = "Chat Message 2"

    message_1 = Message(text=message_text_1, chat_id=chat.id, profile_id=profile.id)
    message_2 = Message(text=message_text_2, chat_id=chat.id, profile_id=profile.id)

    session.add(message_1)
    session.add(message_2)
    session.commit()
    session.refresh(message_1)
    session.refresh(message_2)

    # 특정 채팅의 메시지 목록 조회
    response = client.get(f"/chats/{chat.id}/messages/")
    data = response.json()

    assert response.status_code == 200
    assert len(data) >= 2
    # 메시지가 해당 채팅에 속하는지 확인
    for message in data:
        assert message["text"] in [message_text_1, message_text_2]


def test_two_profiles_messaging(
    client: TestClient, session: Session, profiles: list, chat_with_profiles: Chat
):
    # 두 사용자가 메시지를 주고받는 시나리오 테스트
    profile_1 = profiles[0]
    profile_2 = profiles[1]
    chat = chat_with_profiles

    # User1이 첫 번째 메시지 전송
    message_data_1 = {
        "text": "Hello from User1",
        "chat_id": str(chat.id),
        "profile_id": str(profile_1.id),
    }
    response_1 = client.post("/messages/", json=message_data_1)
    assert response_1.status_code == 200
    data_1 = response_1.json()
    assert data_1["text"] == message_data_1["text"]
    assert "id" in data_1

    # User2가 두 번째 메시지 전송
    message_data_2 = {
        "text": "Hello from User2",
        "chat_id": str(chat.id),
        "profile_id": str(profile_2.id),
    }
    response_2 = client.post("/messages/", json=message_data_2)
    assert response_2.status_code == 200
    data_2 = response_2.json()
    assert data_2["text"] == message_data_2["text"]
    assert "id" in data_2

    # User1이 채팅의 메시지 목록을 조회하여 두 메시지 모두 확인
    response_user1 = client.get(f"/chats/{chat.id}/messages/")
    assert response_user1.status_code == 200
    data_user1 = response_user1.json()
    assert len(data_user1) == 2
    message_texts_user1 = [message["text"] for message in data_user1]
    assert "Hello from User1" in message_texts_user1
    assert "Hello from User2" in message_texts_user1

    # User2도 동일하게 채팅의 메시지 목록을 조회하여 두 메시지 모두 확인
    response_user2 = client.get(f"/chats/{chat.id}/messages/")
    assert response_user2.status_code == 200
    data_user2 = response_user2.json()
    assert len(data_user2) == 2
    message_texts_user2 = [message["text"] for message in data_user2]
    assert "Hello from User1" in message_texts_user2
    assert "Hello from User2" in message_texts_user2
