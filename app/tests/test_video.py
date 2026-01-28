import pytest
import io
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine, select
from sqlmodel.pool import StaticPool
from uuid import uuid4

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
        # 테스트용 프로필 추가
        profile = Profile(name="TestUser", bio="Test Bio")
        session.add(profile)
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


@pytest.fixture(name="profile")
def profile_fixture(session: Session):
    profile = session.exec(select(Profile)).first()
    return profile


def test_upload_video(client: TestClient, profile):
    """비디오 업로드 테스트"""
    # 가짜 비디오 파일 생성
    fake_video = io.BytesIO(b"fake video content")
    fake_video.name = "test.mp4"
    fake_video.content_type = "video/mp4"

    # 비디오 업로드
    response = client.post(
        "/upload/videos/",
        data={
            "object_type": "post",
            "object_id": str(profile.id),
        },
        files=[("files", fake_video)],
    )

    data = response.json()
    assert response.status_code == 200
    assert len(data) == 1
    assert data[0]["media_type"] == "video"
    assert data[0]["filename"] == "test.mp4"
    assert data[0]["content_type"] == "video/mp4"
    assert data[0]["object_type"] == "post"
    assert data[0]["object_id"] == str(profile.id)
    # Mock 데이터 검증
    assert data[0]["duration"] == 30
    assert data[0]["width"] == 1920
    assert data[0]["height"] == 1080
    assert data[0]["video_codec"] == "h264"
    assert data[0]["thumbnail_url"] is not None


def test_upload_multiple_videos(client: TestClient, profile):
    """여러 비디오 업로드 테스트"""
    # 가짜 비디오 파일들 생성
    fake_video_1 = io.BytesIO(b"fake video content 1")
    fake_video_1.name = "test1.mp4"
    fake_video_1.content_type = "video/mp4"

    fake_video_2 = io.BytesIO(b"fake video content 2")
    fake_video_2.name = "test2.mp4"
    fake_video_2.content_type = "video/mp4"

    # 여러 비디오 업로드
    response = client.post(
        "/upload/videos/",
        data={
            "object_type": "post",
            "object_id": str(profile.id),
        },
        files=[
            ("files", fake_video_1),
            ("files", fake_video_2),
        ],
    )

    data = response.json()
    assert response.status_code == 200
    assert len(data) == 2
    assert data[0]["media_type"] == "video"
    assert data[1]["media_type"] == "video"


def test_upload_video_invalid_object_id(client: TestClient):
    """유효하지 않은 object_id로 비디오 업로드 테스트"""
    fake_video = io.BytesIO(b"fake video content")
    fake_video.name = "test.mp4"
    fake_video.content_type = "video/mp4"

    response = client.post(
        "/upload/videos/",
        data={
            "object_type": "post",
            "object_id": "invalid-uuid",
        },
        files=[("files", fake_video)],
    )

    assert response.status_code == 422  # Invalid object_id format


def test_upload_video_skip_non_video(client: TestClient, profile):
    """비디오가 아닌 파일은 건너뛰는지 테스트"""
    # 가짜 이미지 파일 (비디오가 아님)
    fake_image = io.BytesIO(b"fake image content")
    fake_image.name = "test.jpg"
    fake_image.content_type = "image/jpeg"

    response = client.post(
        "/upload/videos/",
        data={
            "object_type": "post",
            "object_id": str(profile.id),
        },
        files=[("files", fake_image)],
    )

    data = response.json()
    assert response.status_code == 200
    assert len(data) == 0  # 비디오가 아니므로 업로드 안됨


def test_get_video_media(client: TestClient, profile):
    """비디오 미디어 조회 테스트"""
    # 먼저 비디오 업로드
    fake_video = io.BytesIO(b"fake video content")
    fake_video.name = "test.mp4"
    fake_video.content_type = "video/mp4"

    upload_response = client.post(
        "/upload/videos/",
        data={
            "object_type": "post",
            "object_id": str(profile.id),
        },
        files=[("files", fake_video)],
    )

    uploaded_media = upload_response.json()
    media_id = uploaded_media[0]["id"]

    # 미디어 조회
    response = client.get(f"/media/{media_id}")
    data = response.json()

    assert response.status_code == 200
    assert data["id"] == media_id
    assert data["media_type"] == "video"
    assert data["duration"] == 30
    assert data["video_codec"] == "h264"


def test_list_video_media(client: TestClient, profile):
    """비디오 미디어 목록 조회 테스트"""
    # 비디오 업로드
    fake_video = io.BytesIO(b"fake video content")
    fake_video.name = "test.mp4"
    fake_video.content_type = "video/mp4"

    client.post(
        "/upload/videos/",
        data={
            "object_type": "post",
            "object_id": str(profile.id),
        },
        files=[("files", fake_video)],
    )

    # 미디어 목록 조회 (object_type 필터)
    response = client.get("/media/?object_type=post")
    data = response.json()

    assert response.status_code == 200
    assert len(data) >= 1
    assert any(media["media_type"] == "video" for media in data)
