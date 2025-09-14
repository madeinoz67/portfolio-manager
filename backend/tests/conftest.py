import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import date
from decimal import Decimal
from dataclasses import dataclass

from src.main import app
from src.database import get_db, Base
from src.models.user import User
from src.models.portfolio import Portfolio
from src.models.stock import Stock
from src.models.user_role import UserRole
from src.core.auth import get_password_hash, create_access_token


SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@dataclass
class TestData:
    """Test data container for common test objects."""
    user: User
    portfolio: Portfolio
    stock: Stock
    access_token: str


@pytest.fixture
def client():
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:
        yield c
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_data(db):
    """Create test data for transaction tests."""
    # Create test user
    user = User(
        email="test@example.com",
        first_name="Test",
        last_name="User",
        password_hash=get_password_hash("testpassword")
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Create test portfolio
    portfolio = Portfolio(
        name="Test Portfolio",
        description="Test portfolio for transaction tests",
        owner_id=user.id
    )
    db.add(portfolio)
    db.commit()
    db.refresh(portfolio)
    
    # Create test stock
    stock = Stock(
        symbol="AAPL",
        company_name="Apple Inc.",
        exchange="NASDAQ",
        current_price=Decimal("150.00")
    )
    db.add(stock)
    db.commit()
    db.refresh(stock)
    
    # Create access token
    access_token = create_access_token(data={"sub": user.email})
    
    return TestData(
        user=user,
        portfolio=portfolio,
        stock=stock,
        access_token=access_token
    )


@pytest.fixture
def valid_jwt_token(test_data):
    """Provide a valid JWT token for testing."""
    return test_data.access_token


def get_admin_jwt_token(db_session) -> str:
    """Create or get JWT token for admin user."""
    # Look for existing admin user or create one
    admin_user = db_session.query(User).filter(User.role == UserRole.ADMIN).first()

    if not admin_user:
        admin_user = User(
            email="admin@test.com",
            first_name="Admin",
            last_name="User",
            password_hash=get_password_hash("adminpassword"),
            role=UserRole.ADMIN,
            is_active=True
        )
        db_session.add(admin_user)
        db_session.commit()
        db_session.refresh(admin_user)

    return create_access_token(data={"sub": admin_user.email})


def get_user_jwt_token(db_session) -> str:
    """Create or get JWT token for regular user."""
    # Look for existing regular user or create one
    regular_user = db_session.query(User).filter(User.role == UserRole.USER).first()

    if not regular_user:
        regular_user = User(
            email="user@test.com",
            first_name="Regular",
            last_name="User",
            password_hash=get_password_hash("userpassword"),
            role=UserRole.USER,
            is_active=True
        )
        db_session.add(regular_user)
        db_session.commit()
        db_session.refresh(regular_user)

    return create_access_token(data={"sub": regular_user.email})


@pytest.fixture
def db_session():
    """Provide database session for testing."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)