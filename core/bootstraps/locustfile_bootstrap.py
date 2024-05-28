import os
import glob
import inspect
from locust import HttpUser
from dotenv import load_dotenv


def load_locustfiles():
    load_dotenv()
    working_dir = os.getenv('WORKING_DIR', '')
    print(f"Working directory: {working_dir}")

    blueprint_dir = os.path.join(working_dir, 'app', 'blueprints')
    print(f"Blueprint directory: {blueprint_dir}")

    locustfile_paths = glob.glob(os.path.join(blueprint_dir, '*', 'locustfile.py'))
    print(f"Found locustfiles: {locustfile_paths}")

    found_user_classes = []

    for path in locustfile_paths:
        print(f"Loading locustfile: {path}")
        with open(path) as f:
            code = compile(f.read(), path, 'exec')
            exec(code, globals())

        # Collect all classes that inherit from HttpUser
        for name, obj in globals().items():
            if inspect.isclass(obj) and issubclass(obj, HttpUser) and obj is not HttpUser:

                unique_name = f"{name}_{os.path.basename(path).split('.')[0]}"
                if unique_name not in globals():
                    found_user_classes.append((unique_name, obj))
                    print(f"Loaded user class: {unique_name}")
                else:
                    print(f"Skipped duplicate user class: {unique_name}")

    if not found_user_classes:
        raise ValueError("No User class found!")


load_locustfiles()
