import pytest
from splent_framework.utils.app_loader import get_create_app_in_testing_mode


@pytest.fixture(scope="session")
def app():
    """The app the features' tests run against (their test_app fixture
    builds it the same way), without resetting the test database:
    test_frozen_urls.py only reads the app, and test_shell.py resets the
    database itself before it adds the accounts it signs in with."""
    return get_create_app_in_testing_mode()
