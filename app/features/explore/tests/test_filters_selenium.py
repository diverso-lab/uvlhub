import pytest

from app.environment.host import get_host_for_selenium_testing
from app.selenium.common import close_driver, initialize_driver

pytestmark = pytest.mark.e2e


def test_filters_panel_displays_all_filter_inputs():
    """Test that all filter inputs are visible on the explore page"""
    driver = initialize_driver()

    try:
        host = get_host_for_selenium_testing()
        driver.get(f"{host}/explore")

        # Check that all filter elements exist
        assert driver.find_element("id", "search-query")
        assert driver.find_element("id", "filter-publication-type")
        assert driver.find_element("id", "filter-tags")
        assert driver.find_element("id", "filter-date-from")
        assert driver.find_element("id", "filter-date-to")
        assert driver.find_element("id", "filter-features-min")
        assert driver.find_element("id", "filter-features-max")
        assert driver.find_element("id", "filter-models-min")
        assert driver.find_element("id", "filter-models-max")
        assert driver.find_element("id", "filter-year")
        assert driver.find_element("id", "filter-only-authors")
        assert driver.find_element("id", "filter-sorting")
        assert driver.find_element("id", "clear-filters")

    finally:
        close_driver(driver)


def test_features_min_input_accepts_numbers():
    """Test that features min input accepts numeric input"""
    driver = initialize_driver()

    try:
        host = get_host_for_selenium_testing()
        driver.get(f"{host}/explore")

        features_min_input = driver.find_element("id", "filter-features-min")
        features_min_input.send_keys("10")

        assert features_min_input.get_attribute("value") == "10"

    finally:
        close_driver(driver)


def test_features_max_input_accepts_numbers():
    """Test that features max input accepts numeric input"""
    driver = initialize_driver()

    try:
        host = get_host_for_selenium_testing()
        driver.get(f"{host}/explore")

        features_max_input = driver.find_element("id", "filter-features-max")
        features_max_input.send_keys("50")

        assert features_max_input.get_attribute("value") == "50"

    finally:
        close_driver(driver)


def test_models_min_input_accepts_numbers():
    """Test that models min input accepts numeric input"""
    driver = initialize_driver()

    try:
        host = get_host_for_selenium_testing()
        driver.get(f"{host}/explore")

        models_min_input = driver.find_element("id", "filter-models-min")
        models_min_input.send_keys("1")

        assert models_min_input.get_attribute("value") == "1"

    finally:
        close_driver(driver)


def test_models_max_input_accepts_numbers():
    """Test that models max input accepts numeric input"""
    driver = initialize_driver()

    try:
        host = get_host_for_selenium_testing()
        driver.get(f"{host}/explore")

        models_max_input = driver.find_element("id", "filter-models-max")
        models_max_input.send_keys("20")

        assert models_max_input.get_attribute("value") == "20"

    finally:
        close_driver(driver)


def test_year_dropdown_has_options():
    """Test that year dropdown has selectable options"""
    driver = initialize_driver()

    try:
        host = get_host_for_selenium_testing()
        driver.get(f"{host}/explore")

        year_select = driver.find_element("id", "filter-year")
        options = year_select.find_elements("tag name", "option")

        # Should have at least "Any year" option plus some years
        assert len(options) > 1

    finally:
        close_driver(driver)


def test_year_dropdown_can_select_year():
    """Test that year can be selected from dropdown"""
    driver = initialize_driver()

    try:
        host = get_host_for_selenium_testing()
        driver.get(f"{host}/explore")

        year_select = driver.find_element("id", "filter-year")
        year_select.send_keys("2023")

        assert year_select.get_attribute("value") == "2023"

    finally:
        close_driver(driver)


def test_only_authors_checkbox_can_be_checked():
    """Test that only_with_authors checkbox can be toggled"""
    driver = initialize_driver()

    try:
        host = get_host_for_selenium_testing()
        driver.get(f"{host}/explore")

        checkbox = driver.find_element("id", "filter-only-authors")
        assert not checkbox.is_selected()

        checkbox.click()
        assert checkbox.is_selected()

    finally:
        close_driver(driver)


def test_only_authors_checkbox_can_be_unchecked():
    """Test that checkbox can be toggled back"""
    driver = initialize_driver()

    try:
        host = get_host_for_selenium_testing()
        driver.get(f"{host}/explore")

        checkbox = driver.find_element("id", "filter-only-authors")
        checkbox.click()
        assert checkbox.is_selected()

        checkbox.click()
        assert not checkbox.is_selected()

    finally:
        close_driver(driver)


def test_clear_filters_button_resets_all_inputs():
    """Test that Clear Filters button resets all filter values"""
    driver = initialize_driver()

    try:
        host = get_host_for_selenium_testing()
        driver.get(f"{host}/explore")

        # Set various filter values
        driver.find_element("id", "search-query").send_keys("test")
        driver.find_element("id", "filter-features-min").send_keys("10")
        driver.find_element("id", "filter-features-max").send_keys("50")
        driver.find_element("id", "filter-models-min").send_keys("1")
        driver.find_element("id", "filter-year").send_keys("2023")
        driver.find_element("id", "filter-only-authors").click()

        # Click clear button
        clear_button = driver.find_element("id", "clear-filters")
        clear_button.click()

        # Verify all inputs are reset
        assert driver.find_element("id", "search-query").get_attribute("value") == ""
        assert driver.find_element("id", "filter-features-min").get_attribute("value") == ""
        assert driver.find_element("id", "filter-features-max").get_attribute("value") == ""
        assert driver.find_element("id", "filter-models-min").get_attribute("value") == ""
        assert driver.find_element("id", "filter-year").get_attribute("value") == ""
        assert not driver.find_element("id", "filter-only-authors").is_selected()

    finally:
        close_driver(driver)


def test_filter_input_validation_min_not_negative():
    """Test that min fields don't accept negative numbers"""
    driver = initialize_driver()

    try:
        host = get_host_for_selenium_testing()
        driver.get(f"{host}/explore")

        features_min = driver.find_element("id", "filter-features-min")
        # HTML5 number input with min=0 should not allow negative
        assert features_min.get_attribute("min") == "0"

    finally:
        close_driver(driver)
