import importlib
from fastapi.testclient import TestClient
from src import app as app_module


def create_client():
    reloaded = importlib.reload(app_module)
    return TestClient(reloaded.app)


def test_root_redirects_to_static_index():
    client = create_client()
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_activity_list():
    client = create_client()
    response = client.get("/activities")

    assert response.status_code == 200
    data = response.json()
    assert "Chess Club" in data
    assert "Programming Class" in data
    assert isinstance(data["Chess Club"]["participants"], list)


def test_signup_for_activity_success():
    client = create_client()
    activity_name = "Chess Club"
    email = "teststudent@mergington.edu"

    response = client.post(f"/activities/{activity_name}/signup", params={"email": email})

    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {activity_name}"}
    assert email in client.get("/activities").json()[activity_name]["participants"]


def test_signup_for_activity_duplicate_returns_400():
    client = create_client()
    activity_name = "Chess Club"
    email = "duplicate@mergington.edu"

    first_response = client.post(f"/activities/{activity_name}/signup", params={"email": email})
    assert first_response.status_code == 200

    second_response = client.post(f"/activities/{activity_name}/signup", params={"email": email})
    assert second_response.status_code == 400
    assert second_response.json()["detail"] == "Student already signed up for this activity"


def test_signup_for_nonexistent_activity_returns_404():
    client = create_client()
    response = client.post("/activities/NoSuchActivity/signup", params={"email": "student@mergington.edu"})

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_participant_success():
    client = create_client()
    activity_name = "Programming Class"
    email = "unregister@mergington.edu"

    signup_response = client.post(f"/activities/{activity_name}/signup", params={"email": email})
    assert signup_response.status_code == 200

    unregister_response = client.delete(f"/activities/{activity_name}/participants", params={"email": email})
    assert unregister_response.status_code == 200
    assert unregister_response.json() == {"message": f"Unregistered {email} from {activity_name}"}
    assert email not in client.get("/activities").json()[activity_name]["participants"]


def test_unregister_missing_participant_returns_404():
    client = create_client()
    response = client.delete("/activities/Gym Class/participants", params={"email": "missing@mergington.edu"})

    assert response.status_code == 404
    assert response.json()["detail"] == "Participant not found for this activity"


def test_unregister_nonexistent_activity_returns_404():
    client = create_client()
    response = client.delete("/activities/NoSuchActivity/participants", params={"email": "student@mergington.edu"})

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"
