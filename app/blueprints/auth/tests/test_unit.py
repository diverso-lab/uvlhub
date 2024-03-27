import pytest
from flask import url_for


@pytest.fixture(scope='module')
def test_client(test_client):
    """
    Extends the test_client fixture to add additional specific data for module testing.
    for module testing (por example, new users)
    """
    with test_client.application.app_context():
        # Add HERE new elements to the database that you want to exist in the test context.
        # DO NOT FORGET to use db.session.add(<element>) and db.session.commit() to save the data.
        pass

    yield test_client


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
