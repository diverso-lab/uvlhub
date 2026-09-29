"""Selenium E2E coverage for the random-generator wizard.

Running this in CI requires the `selenium-hub` docker-compose service to be up
and the web app to be reachable at `http://web:5000`. Locally you can drive
the same test against `http://localhost:5000` — see `app.environment.host`.

The critical scenarios are the full wizard walk ending on step 5, where we
boot Pyodide, install the required wheels, and load the wrapper, and the
step 6 generation flow, where a complete UVL model is produced.
"""

import pytest
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC  # noqa: N812
from selenium.webdriver.support.ui import WebDriverWait

from app.environment.host import get_host_for_selenium_testing
from app.selenium.common import close_driver, initialize_driver

pytestmark = pytest.mark.e2e


def _wait_for_generator_overlay_to_disappear(driver, wait):
    wait.until(lambda d: "Preparing generator" not in d.find_element(By.TAG_NAME, "body").text)


def _submit_next(driver, expected_url_fragment, wait):
    before = driver.current_url
    _wait_for_generator_overlay_to_disappear(driver, wait)

    driver.execute_script("""
        const btn = document.querySelector("button[name='nav'][value='next']");
        const form = btn && btn.form;
        if (!form) throw new Error("next button or parent form missing");
        form.requestSubmit(btn);
        """)

    try:
        wait.until(EC.url_contains(expected_url_fragment))
        _wait_for_generator_overlay_to_disappear(driver, wait)
    except TimeoutException:
        after = driver.current_url
        body = driver.execute_script("return document.body.innerText.slice(0, 500);")
        raise AssertionError(
            f"Navigation to {expected_url_fragment!r} never happened.\n"
            f"before: {before}\nafter: {after}\nbody: {body!r}"
        )


def _set_input_value(driver, name, value):
    field = driver.find_element(By.NAME, name)
    driver.execute_script(
        """
        arguments[0].value = arguments[1];
        arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
        arguments[0].dispatchEvent(new Event('change', { bubbles: true }));
        """,
        field,
        value,
    )


def _go_to_step2(driver, wait, host):
    driver.get(f"{host}/generator/random/step1")
    wait.until(EC.presence_of_element_located((By.NAME, "num_models_val")))
    _wait_for_generator_overlay_to_disappear(driver, wait)
    _submit_next(driver, "/step2", wait)


def _go_to_step3(driver, wait, host):
    _go_to_step2(driver, wait, host)
    _submit_next(driver, "/step3", wait)


def _go_to_step6(driver, wait, host):
    driver.get(f"{host}/generator/random/step1")
    wait.until(EC.presence_of_element_located((By.NAME, "num_models_val")))
    _wait_for_generator_overlay_to_disappear(driver, wait)

    for target in ("/step2", "/step3", "/step4", "/step5", "/step6"):
        _submit_next(driver, target, wait)


def test_step1_numeric_fields_expose_expected_browser_constraints():
    driver = initialize_driver()
    try:
        host = get_host_for_selenium_testing()
        wait = WebDriverWait(driver, 30)

        driver.get(f"{host}/generator/random/step1")
        wait.until(EC.presence_of_element_located((By.NAME, "num_models_val")))
        _wait_for_generator_overlay_to_disappear(driver, wait)

        num_models = driver.find_element(By.NAME, "num_models_val")
        seed = driver.find_element(By.NAME, "seed")

        assert num_models.get_attribute("type") == "number"
        assert num_models.get_attribute("min") == "1"
        assert num_models.get_attribute("max") == "1000"

        assert seed.get_attribute("type") == "number"
        assert seed.get_attribute("min") == "1"

    finally:
        close_driver(driver)


def test_generator_landing_page_reachable():
    driver = initialize_driver()
    try:
        host = get_host_for_selenium_testing()

        driver.get(f"{host}/generator")

        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "h1")))

        body = driver.find_element(By.TAG_NAME, "body").text

        assert "Random generator" in body
        assert "LLM generator" in body
        assert "Available" in body
        assert "Experimental" in body

    finally:
        close_driver(driver)


def test_step2_type_level_enables_arithmetic_level_in_ui():
    driver = initialize_driver()
    try:
        host = get_host_for_selenium_testing()
        wait = WebDriverWait(driver, 30)

        _go_to_step2(driver, wait, host)

        arithmetic = driver.find_element(By.ID, "arithmetic_level")
        type_level = driver.find_element(By.ID, "type_level")

        assert not arithmetic.is_selected()

        if not type_level.is_selected():
            driver.execute_script("arguments[0].click();", type_level)

        wait.until(lambda d: d.find_element(By.ID, "arithmetic_level").is_selected())

        assert driver.find_element(By.ID, "type_level").is_selected()
        assert driver.find_element(By.ID, "arithmetic_level").is_selected()
    finally:
        close_driver(driver)


def test_wizard_preserves_step1_values_after_next_and_previous():
    driver = initialize_driver()
    try:
        host = get_host_for_selenium_testing()
        wait = WebDriverWait(driver, 30)

        driver.get(f"{host}/generator/random/step1")
        wait.until(EC.presence_of_element_located((By.NAME, "num_models_val")))
        _wait_for_generator_overlay_to_disappear(driver, wait)

        _set_input_value(driver, "num_models_val", "7")
        _set_input_value(driver, "seed", "77")
        _set_input_value(driver, "name_prefix", "selenium_demo")

        _submit_next(driver, "/step2", wait)

        previous_button = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "button[name='nav'][value='prev']"))
        )
        driver.execute_script("arguments[0].click();", previous_button)

        wait.until(EC.url_contains("/step1"))
        _wait_for_generator_overlay_to_disappear(driver, wait)

        assert driver.find_element(By.NAME, "num_models_val").get_attribute("value") == "7"
        assert driver.find_element(By.NAME, "seed").get_attribute("value") == "77"
        assert driver.find_element(By.NAME, "name_prefix").get_attribute("value") == "selenium_demo"

    finally:
        close_driver(driver)


def test_llm_page_reachable():
    driver = initialize_driver()
    try:
        host = get_host_for_selenium_testing()
        driver.get(f"{host}/generator/llm")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "h1")))
        body = driver.find_element(By.TAG_NAME, "body").text
        assert "LLM" in body
        # WebGPU is the defining requirement of this page and is always
        # rendered (either the support warning or the live UI), unlike
        # controls that the Pyodide loading modal can transiently cover.
        assert "WebGPU" in body
    finally:
        close_driver(driver)


@pytest.mark.slow
def test_wizard_reaches_step5_with_pyodide_ready():
    """Walk the wizard to step 5 and verify that the browser-side runtime
    finishes booting. A healthy `window.__generatorRuntime` means:

    - every wheel in WHEELS downloaded and micropip-installed OK;
    - `fmgen_wrapper.py` imported without errors;
    - the exposed API (`window.generatorRuntime.generateOne`) is callable.

    The actual generate_models invocation is covered server-side by
    `test_wizard_flow::test_full_happy_path_produces_valid_params`. Running it
    here too would add 20-40s of wall time with little extra value.
    """
    driver = initialize_driver()
    try:
        host = get_host_for_selenium_testing()
        short = WebDriverWait(driver, 30)
        pyodide_wait = WebDriverWait(driver, 180)

        driver.get(f"{host}/generator/random/step1")
        short.until(EC.presence_of_element_located((By.NAME, "num_models_val")))
        _wait_for_generator_overlay_to_disappear(driver, short)
        _submit_next(driver, "/step2", short)

        for target in ("/step3", "/step4", "/step5"):
            short.until(EC.presence_of_element_located((By.CSS_SELECTOR, "button[name='nav'][value='next']")))
            _wait_for_generator_overlay_to_disappear(driver, short)
            _submit_next(driver, target, short)

        pyodide_wait.until(lambda d: d.execute_script("""
                const rt = window.__generatorRuntime;
                if (!rt) return false;
                return rt.then(
                    () => window.__pyodideReady = true,
                    () => window.__pyodideError = true
                ), !!window.__pyodideReady || !!window.__pyodideError;
                """))

        assert driver.execute_script("return window.__pyodideReady === true;")
        boot_error = driver.execute_script("return window.__pyodideError === true;")
        assert not boot_error, "Pyodide bootstrap rejected — "
        "check browser console"
        has_runtime = driver.execute_script(
            "return !!(window.generatorRuntime"
            " && typeof window.generatorRuntime.ready === 'function'"
            " && typeof window.generatorRuntime.generateOne === 'function');"
        )
        assert has_runtime, "window.generatorRuntime API "
        "(ready/generateOne) is not callable"
    finally:
        close_driver(driver)


def test_step2_arithmetic_toggles_arithmetic_minor_levels_visibility():
    driver = initialize_driver()
    try:
        host = get_host_for_selenium_testing()
        wait = WebDriverWait(driver, 30)

        _go_to_step2(driver, wait, host)

        arithmetic = driver.find_element(By.ID, "arithmetic_level")
        feature_cardinality = driver.find_element(By.ID, "feature_cardinality")
        aggregate_functions = driver.find_element(By.ID, "aggregate_functions")

        assert not arithmetic.is_selected()
        assert not feature_cardinality.is_displayed()
        assert not aggregate_functions.is_displayed()

        driver.execute_script("arguments[0].click();", arithmetic)

        wait.until(lambda d: d.find_element(By.ID, "feature_cardinality").is_displayed())
        wait.until(lambda d: d.find_element(By.ID, "aggregate_functions").is_displayed())

        assert feature_cardinality.is_displayed()
        assert aggregate_functions.is_displayed()

        driver.execute_script("arguments[0].click();", arithmetic)

        wait.until(lambda d: not d.find_element(By.ID, "feature_cardinality").is_displayed())
        wait.until(lambda d: not d.find_element(By.ID, "aggregate_functions").is_displayed())

        assert not feature_cardinality.is_displayed()
        assert not aggregate_functions.is_displayed()
    finally:
        close_driver(driver)


def test_step2_configuration_is_propagated_to_step3():
    driver = initialize_driver()
    try:
        host = get_host_for_selenium_testing()
        wait = WebDriverWait(driver, 30)

        _go_to_step2(driver, wait, host)

        feature_cardinality = driver.find_element(By.ID, "feature_cardinality")
        group_cardinality = driver.find_element(By.ID, "group_cardinality")

        driver.execute_script("arguments[0].click();", feature_cardinality)
        driver.execute_script("arguments[0].click();", group_cardinality)

        _submit_next(driver, "/step3", wait)

        wait.until(EC.presence_of_element_located((By.ID, "prob_fc")))

        assert driver.find_element(By.ID, "prob_fc")
        assert driver.find_element(By.ID, "min_feature_cardinality")
        assert driver.find_element(By.ID, "max_feature_cardinality")

        assert driver.find_element(By.ID, "group_cardinality_min")
        assert driver.find_element(By.ID, "group_cardinality_max")

    finally:
        close_driver(driver)


def test_step3_group_cardinality_settings_are_shown_when_enabled():
    driver = initialize_driver()
    try:
        host = get_host_for_selenium_testing()
        wait = WebDriverWait(driver, 30)

        _go_to_step2(driver, wait, host)

        group_cardinality = driver.find_element(By.ID, "group_cardinality")
        driver.execute_script("arguments[0].click();", group_cardinality)

        _submit_next(driver, "/step3", wait)

        wait.until(EC.presence_of_element_located((By.ID, "group_cardinality_min")))

        assert driver.find_element(By.ID, "group_cardinality_min")
        assert driver.find_element(By.ID, "group_cardinality_max")

    finally:
        close_driver(driver)


def test_step3_feature_cardinality_settings_are_shown_when_enabled():
    driver = initialize_driver()
    try:
        host = get_host_for_selenium_testing()
        wait = WebDriverWait(driver, 30)

        _go_to_step2(driver, wait, host)

        feature_cardinality = driver.find_element(By.ID, "feature_cardinality")
        driver.execute_script("arguments[0].click();", feature_cardinality)

        _submit_next(driver, "/step3", wait)

        wait.until(EC.presence_of_element_located((By.ID, "prob_fc")))

        assert driver.find_element(By.ID, "prob_fc")
        assert driver.find_element(By.ID, "min_feature_cardinality")
        assert driver.find_element(By.ID, "max_feature_cardinality")

    finally:
        close_driver(driver)


def test_step6_shows_output_options():
    driver = initialize_driver()
    try:
        host = get_host_for_selenium_testing()
        wait = WebDriverWait(driver, 30)

        _go_to_step6(driver, wait, host)

        assert "/step6" in driver.current_url
        assert driver.find_element(By.ID, "ensure_satisfiable")
        assert driver.find_element(By.ID, "feature_count_suffix")
        assert driver.find_element(By.ID, "constraint_count_suffix")
    finally:
        close_driver(driver)


@pytest.mark.slow
def test_step6_generates_one_uvl_model_with_pyodide():
    driver = initialize_driver()
    try:
        host = get_host_for_selenium_testing()
        wait = WebDriverWait(driver, 30)
        pyodide_wait = WebDriverWait(driver, 180)

        driver.get(f"{host}/generator/random/step1")
        wait.until(EC.presence_of_element_located((By.NAME, "num_models_val")))
        _wait_for_generator_overlay_to_disappear(driver, wait)

        _set_input_value(driver, "num_models_val", "1")
        _set_input_value(driver, "seed", "123")
        _set_input_value(driver, "name_prefix", "selenium")

        for target in ("/step2", "/step3", "/step4", "/step5", "/step6"):
            _submit_next(driver, target, wait)

        pyodide_wait.until(lambda d: d.execute_script("""
            const rt = window.generatorRuntime;

            if (!rt || !rt.ready || !rt.fetchParams || !rt.generateOne) {
                return false;
            }
            if (!window.__seleniumGeneratorPromiseStarted) {
                window.__seleniumGeneratorPromiseStarted = true;

                rt.ready().then(
                    () => window.__seleniumGeneratorReady = true,
                    () => window.__seleniumGeneratorError = true
                );
            }
            return !!window.__seleniumGeneratorReady ||
                !!window.__seleniumGeneratorError;
        """))

        assert driver.execute_script("return window.__seleniumGeneratorReady === true;")
        assert not driver.execute_script("return window.__seleniumGeneratorError === true;")

        generate_btn = wait.until(EC.element_to_be_clickable((By.ID, "generate-btn")))
        driver.execute_script("arguments[0].click();", generate_btn)

        pyodide_wait.until(lambda d: d.find_element(By.ID, "gen-counter").text.strip() == "1 / 1")
        pyodide_wait.until(lambda d: "Done" in d.find_element(By.ID, "gen-panel-title").text)

        rows = driver.find_elements(By.CSS_SELECTOR, "#gen-results .gen-row")
        assert len(rows) == 1
        assert "selenium" in rows[0].text
        assert "ok" in rows[0].text.lower()
        assert "f" in rows[0].text.lower()

        assert driver.find_element(By.ID, "gen-actions").is_displayed()
        assert driver.find_element(By.ID, "download-btn").is_displayed()

        view_btn = driver.find_element(By.CSS_SELECTOR, "#gen-results button[aria-label='View UVL']")
        driver.execute_script("arguments[0].click();", view_btn)

        pyodide_wait.until(EC.visibility_of_element_located((By.ID, "gen-modal-host")))
        assert "features" in driver.find_element(By.ID, "gen-modal-host").text

    finally:
        close_driver(driver)
