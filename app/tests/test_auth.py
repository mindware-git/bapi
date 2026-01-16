import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine, select
from sqlmodel.pool import StaticPool

from ..main import app
from ..database import get_session
from ..models.user import User, OAuthAccount
from ..models.profile import Profile


@pytest.fixture(name="session")
def session_fixture():
    """Create an in-memory SQLite database session for tests."""
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session):
    """Create a TestClient that uses the in-memory database session."""

    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@patch("app.routers.auth.get_user_infos_from_google_token")
def test_google_callback_new_user(
    mock_get_google_user, client: TestClient, session: Session
):
    """
    Test Google callback for a completely new user.
    It should create a new User and a new OAuthAccount.
    """
    # 1. Arrange: Mock the external call to Google
    google_user_id = "123456789"
    user_email = "new.user@example.com"
    mock_get_google_user.return_value = {
        "status": True,
        "user_infos": {"id": google_user_id, "email": user_email},
        "token_data": {
            "access_token": "fake_access_token",
            "refresh_token": "fake_refresh_token",
            "expires_in": 3600,
        },
    }

    # 2. Act: Call the API endpoint
    response = client.post("/auth/callback/google", params={"code": "fake_auth_code"})
    response_data = response.json()

    # 3. Assert: Check the HTTP response
    assert response.status_code == 200
    assert response_data["message"] == "New user created successfully"
    assert response_data["user"]["email"] == user_email

    # 4. Assert: Check the database state
    # Verify User creation
    users = session.exec(select(User)).all()
    assert len(users) == 1
    created_user = users[0]
    assert created_user.email == user_email

    # Verify OAuthAccount creation and linking
    oauth_accounts = session.exec(select(OAuthAccount)).all()
    assert len(oauth_accounts) == 1
    created_oauth = oauth_accounts[0]
    assert created_oauth.provider_user_id == google_user_id
    assert created_oauth.user_id == created_user.id
    assert created_oauth.access_token == "fake_access_token"


@patch("app.routers.auth.get_user_infos_from_google_token")
def test_google_callback_existing_user_new_oauth(
    mock_get_google_user, client: TestClient, session: Session
):
    """
    Test Google callback for an existing user signing in with a new OAuth provider.
    It should not create a new User, but link a new OAuthAccount to the existing user.
    """
    # 1. Arrange: Create an existing user and a linked profile in the database
    existing_user_email = "existing.user@example.com"
    existing_profile = Profile(name=existing_user_email)
    session.add(existing_profile)
    session.flush()  # Get profile.id
    existing_user = User(email=existing_user_email, profile_id=existing_profile.id)
    session.add(existing_user)
    session.commit()
    session.refresh(existing_user)
    session.refresh(existing_profile)

    # Mock the external call to Google
    google_user_id = "987654321"
    mock_get_google_user.return_value = {
        "status": True,
        "user_infos": {"id": google_user_id, "email": existing_user_email},
        "token_data": {"access_token": "another_fake_access_token"},
    }

    # 2. Act: Call the API endpoint
    response = client.post("/auth/callback/google", params={"code": "fake_auth_code"})
    response_data = response.json()

    # 3. Assert: Check the HTTP response
    assert response.status_code == 200
    assert response_data["message"] == "Existing user linked with Google account"
    assert response_data["user"]["email"] == existing_user_email
    assert response_data["user"]["id"] == str(existing_user.id)

    # 4. Assert: Check the database state
    # Verify no new user was created
    users = session.exec(select(User)).all()
    assert len(users) == 1

    # Verify a new OAuthAccount was created and linked
    oauth_accounts = session.exec(select(OAuthAccount)).all()
    assert len(oauth_accounts) == 1
    created_oauth = oauth_accounts[0]
    assert created_oauth.provider_user_id == google_user_id
    assert created_oauth.user_id == existing_user.id


@patch("app.routers.auth.get_user_infos_from_google_token")
def test_google_callback_returning_oauth_user(
    mock_get_google_user, client: TestClient, session: Session
):
    """
    Test Google callback for a returning user who already has a linked OAuth account.
    It should not create any new records and should update the token.
    """
    # 1. Arrange: Create a user and a linked profile, then a linked OAuth account
    user_email = "returning.user@example.com"
    profile = Profile(name=user_email)
    session.add(profile)
    session.flush()  # Get profile.id
    user = User(email=user_email, profile_id=profile.id)
    session.add(user)
    session.commit()
    session.refresh(user)
    session.refresh(profile)

    google_user_id = "1122334455"
    oauth_account = OAuthAccount(
        user_id=user.id,
        oauth_provider="google",
        provider_user_id=google_user_id,
        access_token="old_access_token",
    )
    session.add(oauth_account)
    session.commit()
    session.refresh(oauth_account)

    # Mock the external call to Google
    mock_get_google_user.return_value = {
        "status": True,
        "user_infos": {"id": google_user_id, "email": user.email},
        "token_data": {"access_token": "new_access_token"},
    }

    # 2. Act: Call the API endpoint
    response = client.post("/auth/callback/google", params={"code": "fake_auth_code"})
    response_data = response.json()

    # 3. Assert: Check the HTTP response
    assert response.status_code == 200
    assert response_data["message"] == "Existing user signed in successfully"
    assert response_data["user"]["id"] == str(user.id)

    # 4. Assert: Check the database state
    # Verify no new users or accounts were created
    users = session.exec(select(User)).all()
    assert len(users) == 1
    oauth_accounts = session.exec(select(OAuthAccount)).all()
    assert len(oauth_accounts) == 1

    # Verify the access token was updated
    session.refresh(oauth_account)
    assert oauth_account.access_token == "new_access_token"
