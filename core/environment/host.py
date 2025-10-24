import os

from dotenv import load_dotenv

load_dotenv()


def get_host_for_testing(test_type: str) -> str:
    """
    Get the host URL for testing based on the test type and the working directory.

    Parameters:
    test_type (str): The type of test (either "locust" or "selenium").

    Returns:
    str: The host URL corresponding to the test type and working directory.

    Raises:
    ValueError: If the test type is unknown or the WORKING_DIR value is not mapped.
    """
    # Define host mappings for locust and selenium tests
    host_mapping = {
        "locust": {
            "": "http://localhost:5000",
            "/app/": "http://nginx_web_server_container",
            "/vagrant/": "http://localhost:5000",
        },
        "selenium": {
            "": "http://localhost:5000",
            "/app/": "http://web:5000",
            "/vagrant/": "http://localhost:5000",
        },
    }

    # Check if the provided test type is valid
    if test_type not in host_mapping:
        raise ValueError(f"Unknown test type: {test_type}")

    # Get the working directory from the environment variable
    working_dir = os.getenv("WORKING_DIR", "")

    # Return the host URL based on the working directory
    if working_dir in host_mapping[test_type]:
        return host_mapping[test_type][working_dir]
    else:
        raise ValueError(f"Unknown WORKING_DIR value: {working_dir}")


def get_host_for_locust_testing() -> str:
    """
    Get the host URL for locust testing.

    Returns:
    str: The host URL for locust testing.
    """
    return get_host_for_testing("locust")


def get_host_for_selenium_testing() -> str:
    """
    Get the host URL for selenium testing.

    Returns:
    str: The host URL for selenium testing.
    """
    return get_host_for_testing("selenium")
