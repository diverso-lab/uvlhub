"""End-to-end (browser) checks for the multi-provider login UI.

The real ORCID / GitHub OAuth handshake cannot run against the grid, so these
tests stay at the UI level: every login door is present and wired, and once a
user is in, the remaining identity fields are editable so they can round out
and verify the account. The convergence logic itself is covered by the
service and integration suites.
"""

import time

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from app.environment.host import get_host_for_selenium_testing
from app.selenium.common import close_driver, initialize_driver

pytestmark = pytest.mark.e2e

SEEDED_EMAIL = "user1@example.com"
SEEDED_PASSWORD = "1234"


def _wait(driver, locator, timeout=10):
    return WebDriverWait(driver, timeout).until(EC.presence_of_element_located(locator))


def _login_with_email(driver, host):
    driver.get(f"{host}/login")
    time.sleep(3)
    driver.find_element(By.NAME, "email").send_keys(SEEDED_EMAIL)
    password = driver.find_element(By.NAME, "password")
    password.send_keys(SEEDED_PASSWORD)
    password.send_keys(Keys.RETURN)
    time.sleep(3)


def test_login_page_exposes_all_three_login_methods():
    driver = initialize_driver()
    try:
        host = get_host_for_selenium_testing()
        driver.get(f"{host}/login")

        _wait(driver, (By.NAME, "email"))
        assert driver.find_elements(By.NAME, "password")

        github_link = driver.find_element(By.CSS_SELECTOR, "a[href*='/github/login']")
        orcid_link = driver.find_element(By.CSS_SELECTOR, "a[href*='/orcid/login-email']")
        assert github_link.is_displayed()
        assert orcid_link.is_displayed()
    finally:
        close_driver(driver)


def test_orcid_button_leads_to_the_email_first_step():
    driver = initialize_driver()
    try:
        host = get_host_for_selenium_testing()
        driver.get(f"{host}/login")

        _wait(driver, (By.CSS_SELECTOR, "a[href*='/orcid/login-email']")).click()

        WebDriverWait(driver, 10).until(EC.url_contains("/orcid/login-email"))
        # the email a user types here is what lets ORCID converge onto an
        # existing account instead of creating a new one
        assert driver.find_elements(By.NAME, "email")
    finally:
        close_driver(driver)


def test_profile_edit_lets_the_user_complete_and_verify_the_account():
    driver = initialize_driver()
    try:
        host = get_host_for_selenium_testing()
        _login_with_email(driver, host)

        driver.get(f"{host}/profile/edit")
        name = _wait(driver, (By.NAME, "name"))
        surname = driver.find_element(By.NAME, "surname")
        affiliation = driver.find_element(By.NAME, "affiliation")

        assert name.is_enabled() and surname.is_enabled() and affiliation.is_enabled()
        # the email is shown for verification but not editable as a form field
        assert SEEDED_EMAIL in driver.page_source

        new_affiliation = "E2E Test University"
        affiliation.clear()
        affiliation.send_keys(new_affiliation)
        affiliation.send_keys(Keys.RETURN)

        time.sleep(3)
        driver.get(f"{host}/profile/edit")
        persisted = _wait(driver, (By.NAME, "affiliation")).get_attribute("value")
        assert persisted == new_affiliation
    finally:
        close_driver(driver)


def test_profile_edit_offers_to_connect_the_other_providers():
    driver = initialize_driver()
    try:
        host = get_host_for_selenium_testing()
        _login_with_email(driver, host)

        driver.get(f"{host}/profile/edit")
        _wait(driver, (By.NAME, "name"))

        page = driver.page_source
        # user1 has no linked identities, so both connect entry points show
        assert "/account/connect/github" in page
        assert "/account/connect/orcid" in page
    finally:
        close_driver(driver)
