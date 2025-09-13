import pytest
from app import create_app, db

@pytest.fixture
def app():
    app = create_app("testing")
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def auth_headers(client, app):
    # create a test user
    client.post("/auth/register", json={"username": "test", "password": "test123"})
    # login
    res = client.post("/auth/login", json={"username": "test", "password": "test123"})
    token = res.get_json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
