import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
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
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


def test_create_profile(client: TestClient):
    response = client.post(
        "/profiles/", json={"name": "Deadpond", "bio": "Dive Wilson"}
    )
    data = response.json()

    assert response.status_code == 200
    assert data["name"] == "Deadpond"
    assert data["bio"] == "Dive Wilson"


def test_create_profile_invalid(client: TestClient):
    # bio has an invalid type
    response = client.post(
        "/profiles/",
        json={
            "name": "Deadpond",
            "bio": {"message": "Do you wanna know my secret identity?"},
        },
    )
    assert response.status_code == 422


def test_read_profiles(session: Session, client: TestClient):
    profile_1 = Profile(name="Deadpond", bio="Dive Wilson")
    profile_2 = Profile(name="Rusty-Man", bio="Tommy Sharp")
    session.add(profile_1)
    session.add(profile_2)
    session.commit()

    response = client.get("/profiles/")
    data = response.json()

    assert response.status_code == 200

    assert len(data) == 2
    assert data[0]["name"] == profile_1.name
    assert data[0]["bio"] == profile_1.bio
    assert data[1]["name"] == profile_2.name
    assert data[1]["bio"] == profile_2.bio


def test_read_profile(session: Session, client: TestClient):
    profile_1 = Profile(name="Deadpond", bio="Dive Wilson")
    session.add(profile_1)
    session.commit()

    # UUID 타입의 ID를 문자열로 변환하여 요청
    response = client.get(f"/profiles/{profile_1.id}")
    data = response.json()

    assert response.status_code == 200
    assert data["name"] == profile_1.name
    assert data["bio"] == profile_1.bio


def test_update_profile(session: Session, client: TestClient):
    profile_1 = Profile(name="Deadpond", bio="Dive Wilson")
    session.add(profile_1)
    session.commit()

    response = client.patch(f"/profiles/{profile_1.id}", json={"name": "Deadpuddle"})
    data = response.json()

    assert response.status_code == 200
    assert data["name"] == "Deadpuddle"
    assert data["bio"] == "Dive Wilson"


def test_delete_profile(session: Session, client: TestClient):
    profile_1 = Profile(name="Deadpond", bio="Dive Wilson")
    session.add(profile_1)
    session.commit()

    response = client.delete(f"/profiles/{profile_1.id}")
    profile_in_db = session.get(Profile, profile_1.id)

    assert response.status_code == 200
    assert profile_in_db is None
