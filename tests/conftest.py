import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base, get_db
from app.main import app
from dotenv import load_dotenv
import os

# Loading the environment variables
load_dotenv()

# Using test database URL from the environment variable
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")

@pytest.fixture
def test_db():
    # Create test database engine
    engine = create_engine(TEST_DATABASE_URL)
    
    # Create test database tables
    Base.metadata.create_all(bind=engine)
    
    # Create test SessionLocal
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    try:
        # Create test database session
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()
        # Drop test database tables
        Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client(test_db):
    def override_get_db():
        try:
            yield test_db
        finally:
            test_db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
