import pytest

pytestmark = pytest.mark.e2e

import time

from selenium.common.exceptions import NoSuchElementException

from app.environment.host import get_host_for_selenium_testing
from app.selenium.common import close_driver, initialize_driver


def test_flamapy_index():

    driver = initialize_driver()

    try:
        host = get_host_for_selenium_testing()

        # Open the index page
        driver.get(f"{host}/flamapy")

        # Wait a little while to make sure the page has loaded completely
        time.sleep(4)

        try:

            pass

        except NoSuchElementException:
            raise AssertionError("Test failed!")

    finally:

        # Close the browser
        close_driver(driver)
