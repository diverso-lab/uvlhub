import pytest
from flask import url_for
from app import create_app, db
from app.blueprints.auth.models import User


@pytest.fixture(scope='module')
def test_client():
    flask_app = create_app('testing')

    with flask_app.test_client() as testing_client:
        with flask_app.app_context():
            db.create_all()

            user_test = User(email='test@example.com')
            user_test.set_password('test1234')
            db.session.add(user_test)
            db.session.commit()

            yield testing_client

            db.session.remove()
            db.drop_all()


def login(test_client, email, password):
    """
    Authenticates the user with the credentials provided.

    Args:
        test_client: Flask test client.
        email (str): User's email address.
        password (str): User's password.

    Returns:
        response: POST login request response.
    """
    response = test_client.post('/login', data=dict(
        email=email,
        password=password
    ), follow_redirects=True)
    return response


def logout(test_client):
    """
    Logs out the user.

    Args:
        test_client: Flask test client.

    Returns:
        response: Response to GET request to log out.
    """
    return test_client.get('/logout', follow_redirects=True)


def test_login_success(test_client):
    response = test_client.post('/login', data=dict(
        email='test@example.com',
        password='test1234'
    ), follow_redirects=True)

    assert response.request.path != url_for('auth.login'), "Login was unsuccessful"

    test_client.get('/logout', follow_redirects=True)


def test_login_unsuccessful_bad_email(test_client):
    response = test_client.post('/login', data=dict(
        email='bademail@example.com',
        password='test1234'
    ), follow_redirects=True)

    assert response.request.path == url_for('auth.login'), "Login was unsuccessful"

    test_client.get('/logout', follow_redirects=True)


def test_login_unsuccessful_bad_password(test_client):
    response = test_client.post('/login', data=dict(
        email='test@example.com',
        password='basspassword'
    ), follow_redirects=True)

    assert response.request.path == url_for('auth.login'), "Login was unsuccessful"

    test_client.get('/logout', follow_redirects=True)


def test_edit_profile_page_get(test_client):
    """
    Tests access to the profile editing page via a GET request.
    """
    login_response = login(test_client, 'test@example.com', 'test1234')
    assert login_response.status_code == 200, "Login was unsuccessful."

    response = test_client.get('/profile/edit')
    assert response.status_code == 200, "The profile editing page could not be accessed."
    assert b"Edit profile" in response.data, "The expected content is not present on the page"

    logout(test_client)
