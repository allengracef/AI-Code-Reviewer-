import pytest
import app.services.ai_reviewer as ai_reviewer_module
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from fastapi.testclient import TestClient

from app.database import Base, get_db
from app.main import app as fastapi_app


from app.models import User
from app.services.auth import get_current_user


@pytest.fixture(autouse=True)
def reset_groq_client():
    ai_reviewer_module._groq_client = None


@pytest.fixture(autouse=True)
def mock_review_with_ai_in_review_tests(request):
    if "test_review.py" in request.node.nodeid:
        with patch("app.services.review.review_with_ai") as mock_review:
            mock_review.return_value = {
                "summary": "Code review completed.",
                "issues": [],
            }
            yield mock_review
    else:
        yield


@pytest.fixture(autouse=True)
def override_db():
    """
    Replace the real SQLite DB with an isolated in-memory DB for every test.
    Tables are created fresh and torn down automatically.

    StaticPool is required so that every SQLAlchemy session shares the same
    underlying connection — SQLite in-memory DBs are per-connection, so
    without this the tables created by create_all would be invisible to the
    session used during the request.
    """
    from sqlalchemy.pool import StaticPool

    test_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=test_engine)

    TestSession = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

    def override_get_db():
        db = TestSession()
        try:
            yield db
        finally:
            db.close()

    def override_get_current_user():
        db = TestSession()
        user = db.query(User).filter_by(email="test@example.com").first()
        if not user:
            user = User(
                id=1,
                email="test@example.com",
                name="Test User",
                hashed_password="hashedpassword",
                is_active=True,
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        db.close()
        return user

    fastapi_app.dependency_overrides[get_db] = override_get_db
    fastapi_app.dependency_overrides[get_current_user] = override_get_current_user
    yield
    fastapi_app.dependency_overrides.pop(get_db, None)
    fastapi_app.dependency_overrides.pop(get_current_user, None)
    Base.metadata.drop_all(bind=test_engine)
    test_engine.dispose()


@pytest.fixture()
def client(override_db):
    """
    TestClient built after override_db is active so the in-memory DB tables
    already exist when the app handles requests.

    We do NOT use TestClient as a context manager — that would trigger the
    FastAPI lifespan which calls create_all on the real engine, not the
    in-memory test engine. Instantiating directly skips lifespan events.
    """
    yield TestClient(fastapi_app, raise_server_exceptions=True)

