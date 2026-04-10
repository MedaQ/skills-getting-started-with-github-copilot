"""Integration tests for FastAPI endpoints."""
import pytest
import src.app


@pytest.fixture(autouse=True)
def setup_test_data(sample_activities):
    """Setup test data before each test."""
    src.app.activities = {
        name: {**details, "participants": details["participants"].copy()}
        for name, details in sample_activities.items()
    }


class TestSignupUnregisterFlow:
    """Integration tests for signup and unregister workflows."""

    def test_signup_then_unregister_flow(self, app_with_test_data):
        """Test full flow: signup -> verify in list -> unregister -> verify removed."""
        email = "flow@mergington.edu"
        activity = "Gym%20Class"
        
        # Initially not in activity
        response = app_with_test_data.get("/activities")
        assert email not in response.json()["Gym Class"]["participants"]
        
        # Sign up
        signup_response = app_with_test_data.post(
            f"/activities/{activity}/signup?email={email}"
        )
        assert signup_response.status_code == 200
        
        # Verify in activity
        response = app_with_test_data.get("/activities")
        assert email in response.json()["Gym Class"]["participants"]
        
        # Unregister
        unregister_response = app_with_test_data.delete(
            f"/activities/{activity}/unregister?email={email}"
        )
        assert unregister_response.status_code == 200
        
        # Verify removed from activity
        response = app_with_test_data.get("/activities")
        assert email not in response.json()["Gym Class"]["participants"]

    def test_cannot_signup_twice(self, app_with_test_data):
        """Test that signup fails on second attempt for same user."""
        email = "duplicate@mergington.edu"
        activity = "Gym%20Class"
        
        # First signup succeeds
        response1 = app_with_test_data.post(
            f"/activities/{activity}/signup?email={email}"
        )
        assert response1.status_code == 200
        
        # Second signup fails
        response2 = app_with_test_data.post(
            f"/activities/{activity}/signup?email={email}"
        )
        assert response2.status_code == 400
        
        # Verify only one registration
        response = app_with_test_data.get("/activities")
        participants = response.json()["Gym Class"]["participants"]
        assert participants.count(email) == 1

    def test_signup_unregister_signup_again(self, app_with_test_data):
        """Test that user can signup again after unregistering."""
        email = "retry@mergington.edu"
        activity = "Gym%20Class"
        
        # First signup
        app_with_test_data.post(
            f"/activities/{activity}/signup?email={email}"
        )
        
        # Unregister
        app_with_test_data.delete(
            f"/activities/{activity}/unregister?email={email}"
        )
        
        # Second signup should succeed
        response = app_with_test_data.post(
            f"/activities/{activity}/signup?email={email}"
        )
        assert response.status_code == 200
        
        # Verify registered again
        response = app_with_test_data.get("/activities")
        assert email in response.json()["Gym Class"]["participants"]


class TestParticipantCounting:
    """Integration tests for participant count and availability tracking."""

    def test_availability_updates_on_signup(self, app_with_test_data):
        """Test that availability/spots_left updates correctly on signup."""
        response = app_with_test_data.get("/activities")
        initial = response.json()["Gym Class"]
        initial_spots = initial["max_participants"] - len(initial["participants"])
        
        # Signup
        app_with_test_data.post(
            "/activities/Gym%20Class/signup?email=test@mergington.edu"
        )
        
        response = app_with_test_data.get("/activities")
        updated = response.json()["Gym Class"]
        updated_spots = updated["max_participants"] - len(updated["participants"])
        
        assert updated_spots == initial_spots - 1

    def test_availability_updates_on_unregister(self, app_with_test_data):
        """Test that availability updates correctly on unregister."""
        # Signup first
        app_with_test_data.post(
            "/activities/Gym%20Class/signup?email=test@mergington.edu"
        )
        
        response = app_with_test_data.get("/activities")
        before_unregister = response.json()["Gym Class"]
        spots_before = before_unregister["max_participants"] - len(before_unregister["participants"])
        
        # Unregister
        app_with_test_data.delete(
            "/activities/Gym%20Class/unregister?email=test@mergington.edu"
        )
        
        response = app_with_test_data.get("/activities")
        after_unregister = response.json()["Gym Class"]
        spots_after = after_unregister["max_participants"] - len(after_unregister["participants"])
        
        assert spots_after == spots_before + 1

    def test_multiple_signups_update_count(self, app_with_test_data):
        """Test that multiple signups correctly update participant count."""
        response = app_with_test_data.get("/activities")
        initial_count = len(response.json()["Gym Class"]["participants"])
        
        # Multiple signups
        for i in range(3):
            app_with_test_data.post(
                f"/activities/Gym%20Class/signup?email=user{i}@mergington.edu"
            )
        
        response = app_with_test_data.get("/activities")
        final_count = len(response.json()["Gym Class"]["participants"])
        
        assert final_count == initial_count + 3


class TestEdgeCases:
    """Integration tests for edge cases and special scenarios."""

    def test_unregister_last_participant(self, app_with_test_data):
        """Test unregistering the last participant from an activity."""
        # Activity has 2 participants initially: alice and bob from Chess Club
        response = app_with_test_data.get("/activities")
        initial_count = len(response.json()["Chess Club"]["participants"])
        assert initial_count == 2
        
        # Unregister both
        app_with_test_data.delete(
            "/activities/Chess%20Club/unregister?email=alice@mergington.edu"
        )
        app_with_test_data.delete(
            "/activities/Chess%20Club/unregister?email=bob@mergington.edu"
        )
        
        # Verify activity now has no participants
        response = app_with_test_data.get("/activities")
        final_count = len(response.json()["Chess Club"]["participants"])
        assert final_count == 0

    def test_activities_are_independent(self, app_with_test_data):
        """Test that operations on one activity don't affect others."""
        # Signup to Gym Class
        app_with_test_data.post(
            "/activities/Gym%20Class/signup?email=test@mergington.edu"
        )
        
        # Verify Chess Club is unchanged
        response = app_with_test_data.get("/activities")
        chess_participants = response.json()["Chess Club"]["participants"]
        assert "test@mergington.edu" not in chess_participants
        assert len(chess_participants) == 2  # Still has alice and bob
