import pytest
from fastapi.testclient import TestClient
import os
import sys

# Ensure backend root is on Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from app.database.session import Base, engine, SessionLocal

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    # Create tables in the SQLite shamba_ai.db or test database
    Base.metadata.create_all(bind=engine)
    yield
    # Clean up test user if needed, but since we use standard sqlite we can just yield

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "online"

def test_auth_and_farm_creation():
    # 1. Register a test user
    email = "testfarmer@shamba.ai"
    password = "secretpassword"
    fullname = "Test Farmer"
    
    # Check if user already exists from a previous run and delete it to make test clean
    db = SessionLocal()
    from app.models.models import User
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        db.delete(existing)
        db.commit()
    db.close()

    reg_resp = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": fullname}
    )
    assert reg_resp.status_code == 201
    assert reg_resp.json()["email"] == email

    # 2. Login
    login_resp = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password}
    )
    assert login_resp.status_code == 200
    token_data = login_resp.json()
    assert "access_token" in token_data
    token = token_data["access_token"]
    
    headers = {"Authorization": f"Bearer {token}"}

    # 3. Create Farm
    farm_data = {
        "name": "Test Estate",
        "crop_type": "Coffee",
        "latitude": -1.28,
        "longitude": 36.82,
        "boundary": {"type": "Polygon", "coordinates": [[ [36.82, -1.28], [36.83, -1.28], [36.83, -1.29], [36.82, -1.29], [36.82, -1.28] ]]},
        "area_hectares": 5.4
    }
    
    farm_resp = client.post(
        "/api/v1/farms/",
        json=farm_data,
        headers=headers
    )
    assert farm_resp.status_code == 201
    assert farm_resp.json()["name"] == "Test Estate"
    assert farm_resp.json()["crop_type"] == "Coffee"

    # 4. Get Weather environmental report
    farm_id = farm_resp.json()["id"]
    weather_resp = client.get(
        f"/api/v1/weather/farms/{farm_id}/weather",
        headers=headers
    )
    assert weather_resp.status_code == 200
    assert "soil_moisture" in weather_resp.json()
    assert "stress_score" in weather_resp.json()

    # 5. Fetch prices
    price_resp = client.get(
        "/api/v1/market/prices",
        headers=headers
    )
    assert price_resp.status_code == 200
    assert len(price_resp.json()) > 0
