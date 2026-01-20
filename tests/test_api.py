"""
Test suite for Mergington High School Activities API
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Create a test client for the API"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities to initial state before each test"""
    # Store original state
    original_state = {
        activity: details["participants"].copy() 
        for activity, details in activities.items()
    }
    
    yield
    
    # Restore original state after test
    for activity, participants in original_state.items():
        activities[activity]["participants"] = participants


class TestRootEndpoint:
    """Tests for the root endpoint"""
    
    def test_root_redirects_to_static(self, client):
        """Test that root redirects to static index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestGetActivities:
    """Tests for GET /activities endpoint"""
    
    def test_get_activities_returns_all_activities(self, client):
        """Test that get activities returns all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) > 0
        assert "Soccer Team" in data
        assert "Drama Club" in data
    
    def test_activities_have_required_fields(self, client):
        """Test that each activity has required fields"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, details in data.items():
            assert "description" in details
            assert "schedule" in details
            assert "max_participants" in details
            assert "participants" in details
            assert isinstance(details["participants"], list)


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_successful(self, client):
        """Test successful signup for an activity"""
        # Find an activity with available spots
        activity_name = "Chess Club"
        email = "test@mergington.edu"
        
        # Remove email if it exists (from previous test runs)
        if email in activities[activity_name]["participants"]:
            activities[activity_name]["participants"].remove(email)
        
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        assert email in activities[activity_name]["participants"]
    
    def test_signup_duplicate_fails(self, client):
        """Test that signing up twice fails"""
        activity_name = "Chess Club"
        email = "duplicate@mergington.edu"
        
        # First signup
        client.post(f"/activities/{activity_name}/signup?email={email}")
        
        # Second signup should fail
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "already signed up" in data["detail"].lower()
    
    def test_signup_nonexistent_activity_fails(self, client):
        """Test signup for non-existent activity fails"""
        response = client.post(
            "/activities/NonExistentActivity/signup?email=test@mergington.edu"
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()


class TestUnregisterFromActivity:
    """Tests for DELETE /activities/{activity_name}/unregister endpoint"""
    
    def test_unregister_successful(self, client):
        """Test successful unregistration from an activity"""
        activity_name = "Soccer Team"
        email = "alex@mergington.edu"
        
        # Ensure participant is registered
        if email not in activities[activity_name]["participants"]:
            activities[activity_name]["participants"].append(email)
        
        response = client.delete(
            f"/activities/{activity_name}/unregister?email={email}"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        assert email not in activities[activity_name]["participants"]
    
    def test_unregister_not_registered_fails(self, client):
        """Test unregistering a non-registered participant fails"""
        activity_name = "Chess Club"
        email = "notregistered@mergington.edu"
        
        # Ensure email is not in participants
        if email in activities[activity_name]["participants"]:
            activities[activity_name]["participants"].remove(email)
        
        response = client.delete(
            f"/activities/{activity_name}/unregister?email={email}"
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "not registered" in data["detail"].lower()
    
    def test_unregister_nonexistent_activity_fails(self, client):
        """Test unregister from non-existent activity fails"""
        response = client.delete(
            "/activities/NonExistentActivity/unregister?email=test@mergington.edu"
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()


class TestActivityCapacity:
    """Tests for activity capacity constraints"""
    
    def test_activity_max_participants(self, client):
        """Test that activities have a maximum participant limit"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, details in data.items():
            participants_count = len(details["participants"])
            max_participants = details["max_participants"]
            assert participants_count <= max_participants, \
                f"{activity_name} has more participants than allowed"
