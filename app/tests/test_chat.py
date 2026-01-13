import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine, select
from sqlmodel.pool import StaticPool
from ..main import app
from ..models import Profile, Chat, ProfileChatLink
from ..database import get_session


@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        # 테스트용 프로필 2개 추가
        profile_1 = Profile(name="TestUser1", bio="Test Bio 1")
        profile_2 = Profile(name="TestUser2", bio="Test Bio 2")
        session.add(profile_1)
        session.add(profile_2)
        session.commit()
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
    profiles = session.exec(select(Profile)).all()
    return profiles


def test_create_chat(client: TestClient, profiles: list):
    # 프로필 ID로 채팅 생성
    chat_data = {
        "name": "Test Chat",
        "profile_ids": [str(profiles[0].id), str(profiles[1].id)],
    }
    response = client.post("/chats/", json=chat_data)
    data = response.json()

    assert response.status_code == 200
    assert data["name"] == chat_data["name"]
    assert "id" in data


def test_create_chat_invalid_profile_id(client: TestClient, profiles: list):
    # 유효하지 않은 프로필 ID로 채팅 생성 시도
    chat_data = {
        "name": "Test Chat",
        "profile_ids": ["invalid-uuid"],
    }
    response = client.post("/chats/", json=chat_data)
    assert response.status_code == 422


def test_create_chat_empty_profile_ids(client: TestClient):
    # 빈 프로필 ID 배열로 채팅 생성 시도
    chat_data = {
        "name": "Test Chat",
        "profile_ids": [],
    }
    response = client.post("/chats/", json=chat_data)
    assert response.status_code == 400


def test_create_chat_missing_profile_ids(client: TestClient):
    # 프로필 ID 배열이 없는 경우로 채팅 생성 시도
    chat_data = {
        "name": "Test Chat",
    }
    response = client.post("/chats/", json=chat_data)
    assert response.status_code == 422


def test_read_chats(client: TestClient, profiles: list):
    # 테스트용 채팅 이름 정의
    chat_name_1 = "First Chat"
    chat_name_2 = "Second Chat"

    # 채팅 생성
    chat_1 = Chat(name=chat_name_1)
    chat_2 = Chat(name=chat_name_2)

    with client.app.dependency_overrides[get_session]() as session:
        session.add(chat_1)
        session.add(chat_2)
        session.commit()
        session.refresh(chat_1)
        session.refresh(chat_2)

        # ProfileChatLink 생성
        link_1 = ProfileChatLink(profile_id=profiles[0].id, chat_id=chat_1.id)
        link_2 = ProfileChatLink(profile_id=profiles[1].id, chat_id=chat_2.id)
        session.add(link_1)
        session.add(link_2)
        session.commit()

    # 채팅 목록 조회
    response = client.get("/chats/")
    data = response.json()

    assert response.status_code == 200
    assert len(data) >= 2
    assert data[0]["name"] == chat_name_1
    assert data[1]["name"] == chat_name_2


def test_read_chat(client: TestClient, profiles: list):
    # 채팅 생성
    chat_data = {
        "name": "Test Chat",
        "profile_ids": [str(profiles[0].id)],
    }
    create_response = client.post("/chats/", json=chat_data)
    created_chat = create_response.json()

    # 생성된 채팅 조회
    response = client.get(f"/chats/{created_chat['id']}")
    data = response.json()

    assert response.status_code == 200
    assert data["name"] == chat_data["name"]
    assert data["id"] == created_chat["id"]
