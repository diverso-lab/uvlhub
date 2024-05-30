import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def get_host():

    host_mapping = {
        "": "http://localhost:5000",
        "/app/": "http://nginx_web_server_container",
        "/vagrant/": "http://localhost:5000"
    }
 
    working_dir = os.getenv('WORKING_DIR', "")
    
    if working_dir in host_mapping:
        return host_mapping[working_dir]
    else:
        raise ValueError(f"Unknown WORKING_DIR value: {working_dir}")


def get_host_for_selenium_testing():

    host_mapping = {
        "": "http://localhost:5000",
        "/app/": "http://localhost",
        "/vagrant/": "http://localhost:5000"
    }
 
    working_dir = os.getenv('WORKING_DIR', "")
    
    if working_dir in host_mapping:
        return host_mapping[working_dir]
    else:
        raise ValueError(f"Unknown WORKING_DIR value: {working_dir}")

