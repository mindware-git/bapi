import pytest
import io
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine, select
from sqlmodel.pool import StaticPool
from ..main import app
from ..models.profile import Profile
from ..models.post import Post
from ..models.reaction import Reaction
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


@pytest.fixture(name="posts")
def posts_fixture(client: TestClient, profiles: list):
    # 테스트용 게시물 2개 생성
    fake_image_1 = io.BytesIO(b"fake image content 1")
    fake_image_1.name = "test1.jpg"
    fake_image_1.content_type = "image/jpeg"

    fake_image_2 = io.BytesIO(b"fake image content 2")
    fake_image_2.name = "test2.jpg"
    fake_image_2.content_type = "image/jpeg"

    response_1 = client.post(
        "/posts/",
        data={"text": "First post", "profile_id": str(profiles[0].id)},
        files=[("files", fake_image_1)],
    )

    response_2 = client.post(
        "/posts/",
        data={"text": "Second post", "profile_id": str(profiles[1].id)},
        files=[("files", fake_image_2)],
    )

    return [response_1.json(), response_2.json()]


def test_toggle_reaction(client: TestClient, profiles: list, posts: list):
    # 좋아요 생성
    response = client.post(
        "/reactions/",
        json={
            "post_id": str(posts[0]["id"]),
            "profile_id": str(profiles[0].id),
            "reaction_type": "like",
        },
    )
    data = response.json()
    assert response.status_code == 200
    assert data["post_id"] == str(posts[0]["id"])
    assert data["profile_id"] == str(profiles[0].id)
    assert data["reaction_type"] == "like"

    # 같은 좋아요 다시 요청 (토글 - 삭제)
    response = client.post(
        "/reactions/",
        json={
            "post_id": str(posts[0]["id"]),
            "profile_id": str(profiles[0].id),
            "reaction_type": "like",
        },
    )
    assert response.status_code == 200


def test_toggle_reaction_invalid_post(client: TestClient, profiles: list):
    # 존재하지 않는 게시물에 좋아요 시도
    response = client.post(
        "/reactions/",
        json={
            "post_id": "00000000-0000-0000-0000-000000000000",
            "profile_id": str(profiles[0].id),
            "reaction_type": "like",
        },
    )
    assert response.status_code == 404


def test_toggle_reaction_invalid_profile(client: TestClient, posts: list):
    # 존재하지 않는 프로필로 좋아요 시도
    response = client.post(
        "/reactions/",
        json={
            "post_id": str(posts[0]["id"]),
            "profile_id": "00000000-0000-0000-0000-000000000000",
            "reaction_type": "like",
        },
    )
    assert response.status_code == 404


def test_toggle_reaction_invalid_type(client: TestClient, profiles: list, posts: list):
    # 지원하지 않는 reaction_type
    response = client.post(
        "/reactions/",
        json={
            "post_id": str(posts[0]["id"]),
            "profile_id": str(profiles[0].id),
            "reaction_type": "love",
        },
    )
    assert response.status_code == 400


def test_read_reaction(client: TestClient, profiles: list, posts: list):
    # 좋아요 생성
    create_response = client.post(
        "/reactions/",
        json={
            "post_id": str(posts[0]["id"]),
            "profile_id": str(profiles[0].id),
            "reaction_type": "like",
        },
    )
    created_reaction = create_response.json()

    # 생성된 좋아요 조회
    response = client.get(f"/reactions/{created_reaction['id']}")
    data = response.json()
    assert response.status_code == 200
    assert data["id"] == created_reaction["id"]
    assert data["post_id"] == str(posts[0]["id"])
    assert data["profile_id"] == str(profiles[0].id)


def test_read_reaction_not_found(client: TestClient):
    # 존재하지 않는 좋아요 조회
    response = client.get("/reactions/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


def test_read_reactions_for_post(client: TestClient, profiles: list, posts: list):
    # 첫 번째 게시물에 2개의 좋아요 생성
    client.post(
        "/reactions/",
        json={
            "post_id": str(posts[0]["id"]),
            "profile_id": str(profiles[0].id),
            "reaction_type": "like",
        },
    )
    client.post(
        "/reactions/",
        json={
            "post_id": str(posts[0]["id"]),
            "profile_id": str(profiles[1].id),
            "reaction_type": "like",
        },
    )

    # 첫 번째 게시물의 좋아요 목록 조회
    response = client.get(f"/reactions/post/{posts[0]['id']}")
    data = response.json()
    assert response.status_code == 200
    assert len(data) == 2


def test_read_reactions_for_post_not_found(client: TestClient):
    # 존재하지 않는 게시물의 좋아요 목록 조회
    response = client.get("/reactions/post/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


def test_check_reaction(client: TestClient, profiles: list, posts: list):
    # 좋아요 생성
    client.post(
        "/reactions/",
        json={
            "post_id": str(posts[0]["id"]),
            "profile_id": str(profiles[0].id),
            "reaction_type": "like",
        },
    )

    # 좋아요 확인
    response = client.get(f"/reactions/post/{posts[0]['id']}/profile/{profiles[0].id}")
    data = response.json()
    assert response.status_code == 200
    assert data["post_id"] == str(posts[0]["id"])
    assert data["profile_id"] == str(profiles[0].id)
    assert data["reaction_type"] == "like"


def test_check_reaction_not_found(client: TestClient, profiles: list, posts: list):
    # 좋아요가 없는 경우 확인
    response = client.get(f"/reactions/post/{posts[0]['id']}/profile/{profiles[0].id}")
    assert response.status_code == 404


def test_check_reaction_invalid_post(client: TestClient, profiles: list):
    # 존재하지 않는 게시물로 확인
    response = client.get(
        "/reactions/post/00000000-0000-0000-0000-000000000000/profile/"
        + str(profiles[0].id)
    )
    assert response.status_code == 404


def test_check_reaction_invalid_profile(client: TestClient, posts: list):
    # 존재하지 않는 프로필로 확인
    response = client.get(
        f"/reactions/post/{posts[0]['id']}/profile/00000000-0000-0000-0000-000000000000"
    )
    assert response.status_code == 404
