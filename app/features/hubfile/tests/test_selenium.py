import time

import pytest
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from app.environment.host import get_host_for_selenium_testing
from app.selenium.common import close_driver, initialize_driver

pytestmark = pytest.mark.e2e


def test_hubfile_index():

    driver = initialize_driver()

    try:
        host = get_host_for_selenium_testing()

        # Open the index page
        driver.get(f"{host}/hubfile")

        # Wait a little while to make sure the page has loaded completely
        time.sleep(4)

        try:

            pass

        except NoSuchElementException:
            raise AssertionError("Test failed!")

    finally:

        # Close the browser
        close_driver(driver)


# ---------- LaTeX Export UI Tests ----------


def test_latex_export_button_visible_in_workbench():
    """Verify that the LaTeX export button appears in the workbench."""
    driver = initialize_driver()

    try:
        host = get_host_for_selenium_testing()
        # Navigate to a dataset with models (adjust URL as needed)
        driver.get(f"{host}/dataset/1")

        time.sleep(3)

        # Find the LaTeX export button
        latex_btn = driver.find_element(By.ID, "workbench-export-latex")
        assert latex_btn is not None
        assert latex_btn.is_displayed()

    except NoSuchElementException:
        raise AssertionError("LaTeX export button not found!")

    finally:
        close_driver(driver)


def test_latex_export_modal_opens_on_button_click():
    """Verify that clicking the LaTeX button opens the modal."""
    driver = initialize_driver()

    try:
        host = get_host_for_selenium_testing()
        driver.get(f"{host}/dataset/1")

        time.sleep(3)

        # Click the LaTeX export button
        latex_btn = driver.find_element(By.ID, "workbench-export-latex")
        latex_btn.click()

        time.sleep(2)

        # Wait for modal to appear
        modal = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.ID, "latexExportModal")))

        assert modal.is_displayed()

    except NoSuchElementException:
        raise AssertionError("Modal did not appear!")

    finally:
        close_driver(driver)


def test_latex_export_modal_contains_correct_text():
    """Verify that the modal contains the expected content."""
    driver = initialize_driver()

    try:
        host = get_host_for_selenium_testing()
        driver.get(f"{host}/dataset/1")

        time.sleep(3)

        # Click the LaTeX export button
        latex_btn = driver.find_element(By.ID, "workbench-export-latex")
        latex_btn.click()

        time.sleep(2)

        # Wait for modal and check content
        modal = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.ID, "latexExportModal")))

        modal_text = modal.text
        assert "Your LaTeX package is ready!" in modal_text
        assert ".tex" in modal_text
        assert "uvlhighlight" in modal_text

    except (NoSuchElementException, AssertionError) as e:
        raise AssertionError(f"Modal content verification failed: {e}")

    finally:
        close_driver(driver)


def test_latex_export_modal_download_button_works():
    """Verify that the Download button in the modal initiates a download."""
    driver = initialize_driver()

    try:
        host = get_host_for_selenium_testing()
        driver.get(f"{host}/dataset/1")

        time.sleep(3)

        # Click the LaTeX export button
        latex_btn = driver.find_element(By.ID, "workbench-export-latex")
        latex_btn.click()

        time.sleep(2)

        # Wait for modal
        WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.ID, "latexExportModal")))

        # Click the Download button
        download_btn = driver.find_element(By.ID, "latexExportConfirm")
        assert download_btn.text == "Download"
        assert download_btn.is_enabled()

    except (NoSuchElementException, AssertionError) as e:
        raise AssertionError(f"Download button verification failed: {e}")

    finally:
        close_driver(driver)


def test_latex_export_modal_closes_with_close_button():
    """Verify that clicking the Close button closes the modal."""
    driver = initialize_driver()

    try:
        host = get_host_for_selenium_testing()
        driver.get(f"{host}/dataset/1")

        time.sleep(3)

        # Click the LaTeX export button to open modal
        latex_btn = driver.find_element(By.ID, "workbench-export-latex")
        latex_btn.click()

        time.sleep(2)

        # Wait for modal to be visible
        modal = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.ID, "latexExportModal")))
        assert modal.is_displayed()

        # Click the Close button
        close_btn = driver.find_element(By.XPATH, "//*[@id='latexExportModal']//button[contains(text(), 'Close')]")
        close_btn.click()

        time.sleep(1)

        # Verify modal is hidden
        WebDriverWait(driver, 10).until(EC.invisibility_of_element_located((By.ID, "latexExportModal")))

    except (NoSuchElementException, AssertionError) as e:
        raise AssertionError(f"Modal close verification failed: {e}")

    finally:
        close_driver(driver)


def test_latex_export_modal_header_text():
    """Verify that the modal header displays correct title."""
    driver = initialize_driver()

    try:
        host = get_host_for_selenium_testing()
        driver.get(f"{host}/dataset/1")

        time.sleep(3)

        # Click the LaTeX export button
        latex_btn = driver.find_element(By.ID, "workbench-export-latex")
        latex_btn.click()

        time.sleep(2)

        # Wait for modal
        modal_title = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "latexExportModalLabel")))

        assert modal_title.text == "Export to LaTeX"

    except (NoSuchElementException, AssertionError) as e:
        raise AssertionError(f"Modal title verification failed: {e}")

    finally:
        close_driver(driver)


def test_latex_export_button_has_tooltip():
    """Verify that the LaTeX export button has a tooltip."""
    driver = initialize_driver()

    try:
        host = get_host_for_selenium_testing()
        driver.get(f"{host}/dataset/1")

        time.sleep(3)

        # Find the LaTeX button
        latex_btn = driver.find_element(By.ID, "workbench-export-latex")

        # Check for tooltip attribute
        tooltip_title = latex_btn.get_attribute("title")
        assert tooltip_title == "Export to LaTeX", f"Expected 'Export to LaTeX', got: {tooltip_title}"

        # Optionally, check for data-bs-toggle tooltip
        tooltip_toggle = latex_btn.get_attribute("data-bs-toggle")
        assert tooltip_toggle == "tooltip", f"Expected 'tooltip', got: {tooltip_toggle}"

    except (NoSuchElementException, AssertionError) as e:
        raise AssertionError(f"Tooltip verification failed: {e}")

    finally:
        close_driver(driver)


def test_latex_export_modal_can_be_opened_multiple_times():
    """Verify that the modal can be opened, closed, and opened again."""
    driver = initialize_driver()

    try:
        host = get_host_for_selenium_testing()
        driver.get(f"{host}/dataset/1")

        time.sleep(3)

        latex_btn = driver.find_element(By.ID, "workbench-export-latex")

        # First open
        latex_btn.click()
        time.sleep(1)
        modal = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.ID, "latexExportModal")))
        assert modal.is_displayed()

        # Close
        close_btn = driver.find_element(By.XPATH, "//*[@id='latexExportModal']//button[contains(text(), 'Close')]")
        close_btn.click()
        time.sleep(1)

        # Verify closed
        WebDriverWait(driver, 10).until(EC.invisibility_of_element_located((By.ID, "latexExportModal")))

        # Second open (reusability test)
        latex_btn.click()
        time.sleep(1)
        modal = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.ID, "latexExportModal")))
        assert modal.is_displayed()

    except (NoSuchElementException, AssertionError) as e:
        raise AssertionError(f"Modal reusability test failed: {e}")

    finally:
        close_driver(driver)
