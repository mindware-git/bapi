import pytest
import io
import os
import tempfile
import shutil
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine, select
from sqlmodel.pool import StaticPool

from ..main import app
from ..models.profile import Profile
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


def test_create_post(client: TestClient, profiles: list):
    # 가짜 이미지 파일 생성
    fake_image = io.BytesIO(b"fake image content")
    fake_image.name = "test.jpg"
    fake_image.content_type = "image/jpeg"

    # 첫 번째 프로필 ID로 게시물 생성 (파일 업로드와 함께)
    response = client.post(
        "/posts/",
        data={"text": "Test post content", "profile_id": str(profiles[0].id)},
        files=[("files", fake_image)],
    )
    data = response.json()

    assert response.status_code == 200
    assert data["text"] == "Test post content"
    assert data["profile_id"] == str(profiles[0].id)


def test_create_post_invalid(client: TestClient):
    # 유효하지 않은 프로필 ID로 게시물 생성 시도
    fake_image = io.BytesIO(b"fake image content")
    fake_image.name = "test.jpg"
    fake_image.content_type = "image/jpeg"

    response = client.post(
        "/posts/",
        data={"text": "Test post content", "profile_id": "invalid-uuid"},
        files=[("files", fake_image)],
    )
    assert response.status_code == 422  # Invalid profile_id format


def test_read_posts(client: TestClient, profiles: list):
    # 첫 번째 게시물용 가짜 파일 생성
    fake_image_1 = io.BytesIO(b"fake image content 1")
    fake_image_1.name = "test1.jpg"
    fake_image_1.content_type = "image/jpeg"

    # 두 번째 게시물용 가짜 파일 생성
    fake_image_2 = io.BytesIO(b"fake image content 2")
    fake_image_2.name = "test2.jpg"
    fake_image_2.content_type = "image/jpeg"

    # 첫 번째 게시물 생성
    response_1 = client.post(
        "/posts/",
        data={"text": "First post", "profile_id": str(profiles[0].id)},
        files=[("files", fake_image_1)],
    )

    # 두 번째 게시물 생성
    response_2 = client.post(
        "/posts/",
        data={"text": "Second post", "profile_id": str(profiles[1].id)},
        files=[("files", fake_image_2)],
    )

    # 게시물 조회
    response = client.get("/posts/")
    data = response.json()

    assert response.status_code == 200
    assert len(data) == 2
    assert data[0]["text"] == "First post"
    assert data[1]["text"] == "Second post"


def test_read_post(client: TestClient, profiles: list):
    # 가짜 이미지 파일 생성
    fake_image = io.BytesIO(b"fake image content")
    fake_image.name = "test.jpg"
    fake_image.content_type = "image/jpeg"

    # 게시물 생성
    create_response = client.post(
        "/posts/",
        data={"text": "Test post", "profile_id": str(profiles[0].id)},
        files=[("files", fake_image)],
    )
    created_post = create_response.json()

    # 생성된 게시물 조회
    response = client.get(f"/posts/{created_post['id']}")
    data = response.json()

    assert response.status_code == 200
    assert data["text"] == "Test post"
    assert data["profile_id"] == str(profiles[0].id)


def test_read_profile_posts(client: TestClient, profiles: list):
    # 첫 번째 게시물용 가짜 파일 생성
    fake_image_1 = io.BytesIO(b"fake image content 1")
    fake_image_1.name = "test1.jpg"
    fake_image_1.content_type = "image/jpeg"

    # 두 번째 게시물용 가짜 파일 생성
    fake_image_2 = io.BytesIO(b"fake image content 2")
    fake_image_2.name = "test2.jpg"
    fake_image_2.content_type = "image/jpeg"

    # 첫 번째 프로필의 첫 번째 게시물 생성
    client.post(
        "/posts/",
        data={"text": "First post by TestUser1", "profile_id": str(profiles[0].id)},
        files=[("files", fake_image_1)],
    )

    # 첫 번째 프로필의 두 번째 게시물 생성
    client.post(
        "/posts/",
        data={"text": "Second post by TestUser1", "profile_id": str(profiles[0].id)},
        files=[("files", fake_image_2)],
    )

    # 프로필별 게시물 조회
    response = client.get(f"/profiles/{profiles[0].id}/posts/")
    data = response.json()

    assert response.status_code == 200
    assert len(data) == 2
    assert data[0]["text"] == "First post by TestUser1"
    assert data[1]["text"] == "Second post by TestUser1"
