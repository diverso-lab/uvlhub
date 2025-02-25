from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.firefox.service import Service as FirefoxService
import os


def get_service_driver():
    return os.environ.get("SERVICE_DRIVER", "firefox")


def set_service_driver(driver="firefox"):
    os.environ["SERVICE_DRIVER"] = driver


def initialize_driver():
    # Initialise the browser using WebDriver Manager
    working_dir = os.environ.get("WORKING_DIR", None)
    selenium_hub_url = "http://selenium-hub:4444/wd/hub"
    if working_dir == "/app/":
        if get_service_driver() == "chrome":
            options = webdriver.ChromeOptions()
            driver = webdriver.Remote(
                command_executor=selenium_hub_url,  # URL del Hub
                options=options
            )
        elif get_service_driver() == "firefox":
            # Configuración para usar el navegador Firefox a través de Selenium Grid
            options = webdriver.FirefoxOptions()
            driver = webdriver.Remote(
                command_executor=selenium_hub_url,  # URL del Hub de Selenium
                options=options
            )

        else:
            raise Exception("Driver not supported")
    elif working_dir == "":
        if get_service_driver() == "chrome":
            options = webdriver.ChromeOptions()
            service = ChromeService(ChromeDriverManager().install())
            # if chromeDriverManager does not work for you, uncomment line 23 and comment line 21
            # service = ChromeService('/usr/bin/chromedriver')
            driver = webdriver.Chrome(service=service, options=options)
        elif get_service_driver() == "firefox":
            options = webdriver.FirefoxOptions()
            # Inicializar el servicio y el driver
            service = FirefoxService(GeckoDriverManager().install())
            # if chromeDriverManager does not work for you, uncomment line 30 and comment line 28
            # service = FirefoxService('/snap/bin/geckodriver')
            driver = webdriver.Firefox(service=service, options=options)
        else:
            raise Exception("Driver not supported")
    else:
        raise Exception("Working dir not supported")
    return driver


def close_driver(driver):
    driver.quit()
