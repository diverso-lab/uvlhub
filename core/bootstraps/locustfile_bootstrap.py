import glob
import importlib.util
import inspect
import os

from dotenv import load_dotenv
from locust import HttpUser


def load_locustfiles():
    load_dotenv()
    working_dir = os.getenv("WORKING_DIR", "")
    print(f"Working directory: {working_dir}")

    module_dir = os.path.join(working_dir, "app", "modules")
    print(f"Module directory: {module_dir}")

    locustfile_paths = glob.glob(os.path.join(module_dir, "*", "tests", "locustfile.py"))
    print(f"Found locustfiles: {locustfile_paths}")

    found_user_classes = []

    for path in locustfile_paths:
        print(f"Loading locustfile: {path}")
        module_name = os.path.splitext(os.path.basename(path))[0]
        spec = importlib.util.spec_from_file_location(module_name, path)
        locustfile = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(locustfile)

        # Collect all classes that inherit from HttpUser
        for name, obj in vars(locustfile).items():
            if inspect.isclass(obj) and issubclass(obj, HttpUser) and obj is not HttpUser:
                unique_name = f"{name}_{os.path.basename(path).split('.')[0]}"
                globals()[unique_name] = obj  # Add to globals
                found_user_classes.append((unique_name, obj))
                print(f"Loaded user class: {unique_name}")

    if not found_user_classes:
        raise ValueError("No User class found!")

    return found_user_classes


found_user_classes = load_locustfiles()
print(f"Total user classes loaded: {len(found_user_classes)}")
