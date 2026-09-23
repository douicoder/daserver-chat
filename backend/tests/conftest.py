import os
import secrets
import pytest

os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-testing-only-1234567890"
os.environ["MESSAGE_ENCRYPTION_KEY"] = secrets.token_hex(32)
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["FILE_STORAGE_PATH"] = "./test_storage"

from app import create_app
from app.database.database import Base, engine


@pytest.fixture
def app():
    app = create_app()
    app.config["TESTING"] = True
    yield app
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def db_session():
    from sqlalchemy.orm import sessionmaker
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
