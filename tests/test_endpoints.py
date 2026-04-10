"""Unit tests for FastAPI endpoints."""
import pytest
import src.app


@pytest.fixture(autouse=True)
def setup_test_data(sample_activities):
    """Setup test data before each test."""
    src.app.activities = {
        name: {**details, "participants": details["participants"].copy()}
        for name, details in sample_activities.items()
    }


class TestGetActivities:
    """Tests for GET /activities endpoint."""

    def test_get_activities_returns_all_activities(self, app_with_test_data):
        """Test that GET /activities returns all activities."""
        response = app_with_test_data.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data

    def test_get_activities_structure(self, app_with_test_data):
        """Test that activity data has correct structure."""
        response = app_with_test_data.get("/activities")
        data = response.json()
        activity = data["Chess Club"]
        
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity
        assert isinstance(activity["participants"], list)

    def test_get_activities_includes_participants(self, app_with_test_data):
        """Test that activities include current participants."""
        response = app_with_test_data.get("/activities")
        data = response.json()
        
        assert data["Chess Club"]["participants"] == ["alice@mergington.edu", "bob@mergington.edu"]
        assert data["Programming Class"]["participants"] == ["charlie@mergington.edu"]
        assert data["Gym Class"]["participants"] == []


class TestSignupEndpoint:
    """Tests for POST /activities/{activity_name}/signup endpoint."""

    def test_signup_success(self, app_with_test_data):
        """Test successful signup for an activity."""
        response = app_with_test_data.post(
            "/activities/Gym%20Class/signup?email=new@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "Gym Class" in data["message"]
        assert "new@mergington.edu" in data["message"]

    def test_signup_adds_participant_to_activity(self, app_with_test_data):
        """Test that signup actually adds the participant."""
        app_with_test_data.post(
            "/activities/Gym%20Class/signup?email=new@mergington.edu"
        )
        
        response = app_with_test_data.get("/activities")
        data = response.json()
        assert "new@mergington.edu" in data["Gym Class"]["participants"]

    def test_signup_duplicate_participant_fails(self, app_with_test_data):
        """Test that signup fails when participant already registered."""
        response = app_with_test_data.post(
            "/activities/Chess%20Club/signup?email=alice@mergington.edu"
        )
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"].lower()

    def test_signup_nonexistent_activity_fails(self, app_with_test_data):
        """Test that signup fails for non-existent activity."""
        response = app_with_test_data.post(
            "/activities/Fake%20Club/signup?email=test@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    def test_signup_multiple_users_same_activity(self, app_with_test_data):
        """Test that multiple different users can sign up for same activity."""
        # First signup
        response1 = app_with_test_data.post(
            "/activities/Gym%20Class/signup?email=user1@mergington.edu"
        )
        assert response1.status_code == 200
        
        # Second signup
        response2 = app_with_test_data.post(
            "/activities/Gym%20Class/signup?email=user2@mergington.edu"
        )
        assert response2.status_code == 200
        
        # Verify both are in the activity
        response = app_with_test_data.get("/activities")
        data = response.json()
        assert "user1@mergington.edu" in data["Gym Class"]["participants"]
        assert "user2@mergington.edu" in data["Gym Class"]["participants"]


class TestUnregisterEndpoint:
    """Tests for DELETE /activities/{activity_name}/unregister endpoint."""

    def test_unregister_success(self, app_with_test_data):
        """Test successful unregister from an activity."""
        response = app_with_test_data.delete(
            "/activities/Chess%20Club/unregister?email=alice@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "Unregistered" in data["message"]
        assert "alice@mergington.edu" in data["message"]

    def test_unregister_removes_participant(self, app_with_test_data):
        """Test that unregister actually removes the participant."""
        app_with_test_data.delete(
            "/activities/Chess%20Club/unregister?email=alice@mergington.edu"
        )
        
        response = app_with_test_data.get("/activities")
        data = response.json()
        assert "alice@mergington.edu" not in data["Chess Club"]["participants"]

    def test_unregister_nonexistent_participant_fails(self, app_with_test_data):
        """Test that unregister fails when participant not registered."""
        response = app_with_test_data.delete(
            "/activities/Gym%20Class/unregister?email=notregistered@mergington.edu"
        )
        assert response.status_code == 400
        data = response.json()
        assert "not registered" in data["detail"].lower()

    def test_unregister_nonexistent_activity_fails(self, app_with_test_data):
        """Test that unregister fails for non-existent activity."""
        response = app_with_test_data.delete(
            "/activities/Fake%20Club/unregister?email=test@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    def test_unregister_preserves_other_participants(self, app_with_test_data):
        """Test that unregistering one participant doesn't affect others."""
        app_with_test_data.delete(
            "/activities/Chess%20Club/unregister?email=alice@mergington.edu"
        )
        
        response = app_with_test_data.get("/activities")
        data = response.json()
        assert "bob@mergington.edu" in data["Chess Club"]["participants"]
        assert "alice@mergington.edu" not in data["Chess Club"]["participants"]
