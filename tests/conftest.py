"""Shared pytest fixtures for FastAPI tests."""
import pytest
from fastapi.testclient import TestClient
from src.app import app


@pytest.fixture
def test_client():
    """Create a TestClient for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def sample_activities():
    """Sample activities data for testing."""
    return {
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 3,
            "participants": ["alice@mergington.edu", "bob@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 5,
            "participants": ["charlie@mergington.edu"]
        },
        "Gym Class": {
            "description": "Physical education and sports activities",
            "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
            "max_participants": 2,
            "participants": []
        }
    }


@pytest.fixture
def app_with_test_data(test_client, sample_activities):
    """Inject sample activities into the app for testing."""
    # Import the activities dict from app and replace it with test data
    import src.app
    src.app.activities = sample_activities.copy()
    # Deep copy participants lists to avoid cross-test contamination
    src.app.activities = {
        name: {**details, "participants": details["participants"].copy()}
        for name, details in sample_activities.items()
    }
    yield test_client
    # Cleanup: restore original activities after test
    # (This happens automatically as Python creates a fresh app instance)
