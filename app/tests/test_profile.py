import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine, select
from sqlmodel.pool import StaticPool
import io
import os
import shutil
from PIL import Image

from app.main import app
from app.database import get_session
from app.models.profile import Profile
from app.models.media import Media


# Fixture to create an in-memory SQLite database session for tests
@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


# Fixture to create a TestClient that uses the in-memory database
@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


def test_update_profile_avatar(client: TestClient, session: Session):
    """
    Test updating a profile's avatar.
    """
    # 1. Arrange: Create a profile to update
    profile = Profile(name="testuseravatar")
    session.add(profile)
    session.commit()
    session.refresh(profile)

    # Create a dummy image file in memory (a simple 1x1 red pixel PNG)
    img_byte_arr = io.BytesIO()
    image = Image.new("RGB", (1, 1), "red")
    image.save(img_byte_arr, format="PNG")
    img_byte_arr.seek(0)

    # 2. Act: Call the API endpoint to upload the avatar
    response = client.patch(
        f"/profiles/{profile.id}/avatar",
        files={"file": ("test_avatar.png", img_byte_arr, "image/png")},
    )

    # 3. Assert: Check the HTTP response
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["id"] == str(profile.id)
    assert response_data["avatar"] is not None
    assert response_data["avatar"] != "/static/images/originals/default_avatar.png"
    assert response_data["avatar"].startswith("/uploads/")

    # 4. Assert: Check the database state
    session.refresh(profile)
    assert profile.avatar == response_data["avatar"]

    # Check that a Media object was created
    media = session.exec(
        select(Media).where(Media.object_id == profile.id)
    ).one_or_none()
    assert media is not None
    assert media.object_type == "profile_avatar"
    assert media.original_url == profile.avatar
    assert media.content_type == "image/png"

    # 5. Assert: Check if files were created and then cleanup
    # media.original_url is like /uploads/<uuid>/<filename.png>
    # The path on disk is relative to the project root, so we remove the leading '/'
    upload_subdir = os.path.dirname(media.original_url.lstrip("/"))
    assert os.path.isdir(upload_subdir)

    original_filepath = media.original_url.lstrip("/")
    thumbnail_filepath = media.thumbnail_url.lstrip("/")

    assert os.path.exists(original_filepath)
    assert os.path.exists(thumbnail_filepath)

    # Cleanup created directory and its contents
    shutil.rmtree(upload_subdir)
