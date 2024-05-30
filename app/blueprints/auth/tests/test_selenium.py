from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time

from core.environment.host import get_host_for_selenium_testing


# Initializes the browser options
options = webdriver.ChromeOptions()

# Inicializa el navegador utilizando WebDriver Manager
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

try:

    host = get_host_for_selenium_testing()

    # Abre la página de login
    driver.get(f'{host}/login')

    # Espera un poco para asegurar que la página se ha cargado completamente
    time.sleep(2)

    # Encuentra el campo de usuario y contraseña e ingresa los valores
    email_field = driver.find_element(By.NAME, 'email')
    password_field = driver.find_element(By.NAME, 'password')

    email_field.send_keys('user1@example.com')
    password_field.send_keys('1234')

    # Envía el formulario
    password_field.send_keys(Keys.RETURN)

    # Espera un poco para asegurar que la acción se ha completado
    time.sleep(4)

    # Verifica el resultado
    if 'Login successful!' in driver.page_source:
        print('Test passed!')
    else:
        print('Test failed!')

finally:
    # Cierra el navegador
    driver.quit()
