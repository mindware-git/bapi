import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool
from ..main import app
from ..models.profile import Profile
from ..models.user import User
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


def test_create_user_with_profile(session: Session):
    # 1. 더미 Profile 생성
    profile = Profile(name="테스트유저", bio="테스트용 프로필")

    # 2. Profile DB 저장
    session.add(profile)
    session.commit()
    session.refresh(profile)  # DB에서 생성된 ID를 가져오기 위해 refresh

    # 3. User 생성 (생성된 Profile의 ID 사용)
    user = User(email="test@example.com", profile_id=profile.id)

    # 4. User DB 저장
    session.add(user)
    session.commit()
    session.refresh(user)  # DB에서 생성된 ID를 가져오기 위해 refresh

    # 5. 검증
    assert user.id is not None
    assert user.email == "test@example.com"
    assert user.profile_id == profile.id
    assert user.is_active is True
    assert user.is_superuser is False

    # DB에서 User 다시 조회해서 데이터 확인
    user_from_db = session.get(User, user.id)
    assert user_from_db is not None
    assert user_from_db.email == "test@example.com"
    assert user_from_db.profile_id == profile.id

    # 연결된 Profile도 확인
    profile_from_db = session.get(Profile, profile.id)
    assert profile_from_db is not None
    assert profile_from_db.name == "테스트유저"
    assert profile_from_db.bio == "테스트용 프로필"
