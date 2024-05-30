from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time

# Ruta del controlador del navegador. Asegúrate de tener el driver adecuado (por ejemplo, chromedriver) instalado y configurado.
driver_path = '/path/to/chromedriver'  # Cambia esto a la ruta real de tu chromedriver

# Inicializa el navegador
driver = webdriver.Chrome(executable_path=driver_path)

try:
    # Abre la página de login
    driver.get('http://localhost/login')

    # Espera un poco para asegurar que la página se ha cargado completamente
    time.sleep(2)

    # Encuentra el campo de usuario y contraseña e ingresa los valores
    username_field = driver.find_element(By.NAME, 'username')
    password_field = driver.find_element(By.NAME, 'password')

    username_field.send_keys('admin')
    password_field.send_keys('password')

    # Envía el formulario
    password_field.send_keys(Keys.RETURN)

    # Espera un poco para asegurar que la acción se ha completado
    time.sleep(2)

    # Verifica el resultado
    if 'Login successful!' in driver.page_source:
        print('Test passed!')
    else:
        print('Test failed!')

finally:
    # Cierra el navegador
    driver.quit()
