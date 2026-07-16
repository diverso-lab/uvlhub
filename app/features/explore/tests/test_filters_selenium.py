import pytest

pytestmark = pytest.mark.e2e


class TestExploreFiltersFrontend:
    """Frontend tests for the new search filters using Selenium"""

    def test_filters_panel_displays_all_filter_inputs(self, selenium_driver):
        """Test that all filter inputs are visible on the explore page"""
        selenium_driver.get("http://localhost:5000/explore")

        # Check that all filter elements exist
        assert selenium_driver.find_element("id", "search-query")
        assert selenium_driver.find_element("id", "filter-publication-type")
        assert selenium_driver.find_element("id", "filter-tags")
        assert selenium_driver.find_element("id", "filter-date-from")
        assert selenium_driver.find_element("id", "filter-date-to")
        assert selenium_driver.find_element("id", "filter-features-min")
        assert selenium_driver.find_element("id", "filter-features-max")
        assert selenium_driver.find_element("id", "filter-models-min")
        assert selenium_driver.find_element("id", "filter-models-max")
        assert selenium_driver.find_element("id", "filter-size-min")
        assert selenium_driver.find_element("id", "filter-size-max")
        assert selenium_driver.find_element("id", "filter-files-min")
        assert selenium_driver.find_element("id", "filter-files-max")
        assert selenium_driver.find_element("id", "filter-year")
        assert selenium_driver.find_element("id", "filter-only-authors")
        assert selenium_driver.find_element("id", "filter-sorting")
        assert selenium_driver.find_element("id", "clear-filters")

    def test_features_min_input_accepts_numbers(self, selenium_driver):
        """Test that features min input accepts numeric input"""
        selenium_driver.get("http://localhost:5000/explore")

        features_min_input = selenium_driver.find_element("id", "filter-features-min")
        features_min_input.send_keys("10")

        assert features_min_input.get_attribute("value") == "10"

    def test_features_max_input_accepts_numbers(self, selenium_driver):
        """Test that features max input accepts numeric input"""
        selenium_driver.get("http://localhost:5000/explore")

        features_max_input = selenium_driver.find_element("id", "filter-features-max")
        features_max_input.send_keys("50")

        assert features_max_input.get_attribute("value") == "50"

    def test_models_min_input_accepts_numbers(self, selenium_driver):
        """Test that models min input accepts numeric input"""
        selenium_driver.get("http://localhost:5000/explore")

        models_min_input = selenium_driver.find_element("id", "filter-models-min")
        models_min_input.send_keys("1")

        assert models_min_input.get_attribute("value") == "1"

    def test_models_max_input_accepts_numbers(self, selenium_driver):
        """Test that models max input accepts numeric input"""
        selenium_driver.get("http://localhost:5000/explore")

        models_max_input = selenium_driver.find_element("id", "filter-models-max")
        models_max_input.send_keys("20")

        assert models_max_input.get_attribute("value") == "20"

    def test_size_min_input_accepts_numbers(self, selenium_driver):
        """Test that size min input accepts numeric input"""
        selenium_driver.get("http://localhost:5000/explore")

        size_min_input = selenium_driver.find_element("id", "filter-size-min")
        size_min_input.send_keys("10")

        assert size_min_input.get_attribute("value") == "10"

    def test_size_max_input_accepts_numbers(self, selenium_driver):
        """Test that size max input accepts numeric input"""
        selenium_driver.get("http://localhost:5000/explore")

        size_max_input = selenium_driver.find_element("id", "filter-size-max")
        size_max_input.send_keys("500")

        assert size_max_input.get_attribute("value") == "500"

    def test_files_min_input_accepts_numbers(self, selenium_driver):
        """Test that files min input accepts numeric input"""
        selenium_driver.get("http://localhost:5000/explore")

        files_min_input = selenium_driver.find_element("id", "filter-files-min")
        files_min_input.send_keys("1")

        assert files_min_input.get_attribute("value") == "1"

    def test_files_max_input_accepts_numbers(self, selenium_driver):
        """Test that files max input accepts numeric input"""
        selenium_driver.get("http://localhost:5000/explore")

        files_max_input = selenium_driver.find_element("id", "filter-files-max")
        files_max_input.send_keys("100")

        assert files_max_input.get_attribute("value") == "100"

    def test_year_dropdown_has_options(self, selenium_driver):
        """Test that year dropdown has selectable options"""
        selenium_driver.get("http://localhost:5000/explore")

        year_select = selenium_driver.find_element("id", "filter-year")
        options = year_select.find_elements("tag name", "option")

        # Should have at least "Any year" option plus some years
        assert len(options) > 1

    def test_year_dropdown_can_select_year(self, selenium_driver):
        """Test that year can be selected from dropdown"""
        selenium_driver.get("http://localhost:5000/explore")

        year_select = selenium_driver.find_element("id", "filter-year")
        year_select.send_keys("2023")

        assert year_select.get_attribute("value") == "2023"

    def test_only_authors_checkbox_can_be_checked(self, selenium_driver):
        """Test that only_with_authors checkbox can be toggled"""
        selenium_driver.get("http://localhost:5000/explore")

        checkbox = selenium_driver.find_element("id", "filter-only-authors")
        assert not checkbox.is_selected()

        checkbox.click()
        assert checkbox.is_selected()

    def test_only_authors_checkbox_can_be_unchecked(self, selenium_driver):
        """Test that checkbox can be toggled back"""
        selenium_driver.get("http://localhost:5000/explore")

        checkbox = selenium_driver.find_element("id", "filter-only-authors")
        checkbox.click()
        assert checkbox.is_selected()

        checkbox.click()
        assert not checkbox.is_selected()

    def test_clear_filters_button_resets_all_inputs(self, selenium_driver):
        """Test that Clear Filters button resets all filter values"""
        selenium_driver.get("http://localhost:5000/explore")

        # Set various filter values
        selenium_driver.find_element("id", "search-query").send_keys("test")
        selenium_driver.find_element("id", "filter-features-min").send_keys("10")
        selenium_driver.find_element("id", "filter-features-max").send_keys("50")
        selenium_driver.find_element("id", "filter-models-min").send_keys("1")
        selenium_driver.find_element("id", "filter-year").send_keys("2023")
        selenium_driver.find_element("id", "filter-only-authors").click()

        # Click clear button
        clear_button = selenium_driver.find_element("id", "clear-filters")
        clear_button.click()

        # Verify all inputs are reset
        assert selenium_driver.find_element("id", "search-query").get_attribute("value") == ""
        assert selenium_driver.find_element("id", "filter-features-min").get_attribute("value") == ""
        assert selenium_driver.find_element("id", "filter-features-max").get_attribute("value") == ""
        assert selenium_driver.find_element("id", "filter-models-min").get_attribute("value") == ""
        assert selenium_driver.find_element("id", "filter-year").get_attribute("value") == ""
        assert not selenium_driver.find_element("id", "filter-only-authors").is_selected()

    def test_filter_input_validation_min_not_negative(self, selenium_driver):
        """Test that min fields don't accept negative numbers"""
        selenium_driver.get("http://localhost:5000/explore")

        features_min = selenium_driver.find_element("id", "filter-features-min")
        # HTML5 number input with min=0 should not allow negative
        assert features_min.get_attribute("min") == "0"
