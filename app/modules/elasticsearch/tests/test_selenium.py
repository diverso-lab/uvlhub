from selenium.common.exceptions import NoSuchElementException
import time

from core.environment.host import get_host_for_selenium_testing
from core.selenium.common import initialize_driver, close_driver


def test_elasticsearch_index():

    driver = initialize_driver()

    try:
        host = get_host_for_selenium_testing()

        # Open the index page
        driver.get(f"{host}/elasticsearch")

        # Wait a little while to make sure the page has loaded completely
        time.sleep(4)

        try:

            pass

        except NoSuchElementException:
            raise AssertionError("Test failed!")

    finally:

        # Close the browser
        close_driver(driver)


# Call the test function
test_elasticsearch_index()
