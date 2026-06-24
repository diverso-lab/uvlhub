"""Selenium E2E coverage for the random-generator wizard.

Running this in CI requires the `selenium-hub` docker-compose service to be up
and the web app to be reachable at `http://web:5000`. Locally you can drive
the same test against `http://localhost:5000` — see `app.environment.host`.

The critical scenario is the full wizard walk ending on step 5, where we boot
Pyodide, install ~20 wheels, and load the wrapper. Once the runtime promise
resolves, the browser-side stack is healthy — the actual `generate_models`
call is already exercised server-side by `test_wizard_flow.py`.
"""

import pytest

pytestmark = pytest.mark.e2e
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from app.environment.host import get_host_for_selenium_testing
from app.selenium.common import close_driver, initialize_driver


def _submit_next(driver, expected_url_fragment, wait):
    """Submit the current step's form via `form.requestSubmit()`.

    We bypass `button.click()` because on steps 1-4 the Pyodide loading modal
    sits on top of the Next button and intercepts pointer events."""
    before = driver.current_url
    driver.execute_script("""
        const btn = document.querySelector("button[name='nav'][value='next']");
        const form = btn && btn.form;
        if (!form) throw new Error("next button or parent form missing");
        form.requestSubmit(btn);
        """)
    try:
        wait.until(EC.url_contains(expected_url_fragment))
    except TimeoutException:
        after = driver.current_url
        body = driver.execute_script("return document.body.innerText.slice(0, 400);")
        raise AssertionError(
            f"navigation to {expected_url_fragment!r} never happened.\n"
            f"  before: {before}\n  after:  {after}\n  body: {body!r}"
        )


def test_generator_landing_shows_both_cards():
    driver = initialize_driver()
    try:
        host = get_host_for_selenium_testing()
        driver.get(f"{host}/generator")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "h1")))
        body = driver.find_element(By.TAG_NAME, "body").text
        assert "Random generator" in body
        assert "LLM generator" in body
        assert "Coming soon" in body
    finally:
        close_driver(driver)


def test_llm_placeholder_page_reachable():
    driver = initialize_driver()
    try:
        host = get_host_for_selenium_testing()
        driver.get(f"{host}/generator/llm")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "h1")))
        body = driver.find_element(By.TAG_NAME, "body").text
        assert "Coming soon" in body
    finally:
        close_driver(driver)


@pytest.mark.slow
def test_wizard_reaches_step5_with_pyodide_ready():
    """Walk the wizard to step 5 and verify that the browser-side runtime
    finishes booting. A healthy `window.__generatorRuntime` means:

    - every wheel in WHEELS downloaded and micropip-installed OK;
    - `fmgen_wrapper.py` imported without errors;
    - the exposed API (`window.generatorRuntime.generate`) is callable.

    The actual generate_models invocation is covered server-side by
    `test_wizard_flow::test_full_happy_path_produces_valid_params`. Running it
    here too would add 20-40s of wall time with little extra value.
    """
    driver = initialize_driver()
    try:
        host = get_host_for_selenium_testing()
        short = WebDriverWait(driver, 20)
        pyodide_wait = WebDriverWait(driver, 180)

        # Step 1 → 2: defaults are already valid, just submit.
        driver.get(f"{host}/generator/random/step1")
        short.until(EC.presence_of_element_located((By.NAME, "num_models_val")))
        _submit_next(driver, "/step2", short)

        # Steps 2 → 5: accept defaults.
        for target in ("/step3", "/step4", "/step5"):
            short.until(EC.presence_of_element_located((By.CSS_SELECTOR, "button[name='nav'][value='next']")))
            _submit_next(driver, target, short)

        # Wait for Pyodide to finish booting. The bundle stores a Promise at
        # window.__generatorRuntime and resolves it once wheels + wrapper are
        # loaded; catching the resolution is the contract we care about.
        pyodide_wait.until(lambda d: d.execute_script("""
                const rt = window.__generatorRuntime;
                if (!rt) return false;
                return rt.then(() => window.__pyodideReady = true, () => window.__pyodideError = true),
                       !!window.__pyodideReady || !!window.__pyodideError;
                """))
        boot_error = driver.execute_script("return window.__pyodideError === true;")
        assert not boot_error, "Pyodide bootstrap rejected — check browser console"
        has_runtime = driver.execute_script(
            "return !!(window.generatorRuntime && typeof window.generatorRuntime.generate === 'function');"
        )
        assert has_runtime, "window.generatorRuntime.generate is not callable"
    finally:
        close_driver(driver)
