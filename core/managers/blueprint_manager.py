# blueprint_manager.py
import os
import importlib.util
from flask import Blueprint


class BlueprintManager:
    def __init__(self, app):
        self.app = app
        self.base_dir = os.path.abspath(os.path.dirname(__file__))
        working_dir = os.getenv('WORKING_DIR', '')
        self.blueprints_dir = os.path.join(working_dir, 'app/blueprints')

    def register_blueprints(self):
        self.app.blueprints = {}
        self.app.blueprint_url_prefixes = {}
        for blueprint_name in os.listdir(self.blueprints_dir):
            blueprint_path = os.path.join(self.blueprints_dir, blueprint_name)
            if (os.path.isdir(blueprint_path) and not blueprint_name.startswith('__') and
                    os.path.exists(os.path.join(blueprint_path, '__init__.py')) and
                    blueprint_name != '.pytest_cache'):
                try:
                    routes_module = importlib.import_module(f'app.blueprints.{blueprint_name}.routes')
                    for item in dir(routes_module):
                        if isinstance(getattr(routes_module, item), Blueprint):
                            blueprint = getattr(routes_module, item)
                            self.app.register_blueprint(blueprint)
                except ModuleNotFoundError as e:
                    print(
                        f"Error registering blueprints: Could not load the module "
                        f"for Blueprint '{blueprint_name}': {e}")

    def register_blueprint(self, blueprint_name):
        blueprint_path = os.path.join(self.blueprints_dir, blueprint_name)
        if os.path.isdir(blueprint_path) and not blueprint_name.startswith('__'):
            try:
                routes_module = importlib.import_module(f'app.blueprints.{blueprint_name}.routes')
                for item in dir(routes_module):
                    if isinstance(getattr(routes_module, item), Blueprint):
                        blueprint = getattr(routes_module, item)
                        self.app.register_blueprint(blueprint)
                return
            except ModuleNotFoundError as e:
                print(f"Could not load the module for Blueprint '{blueprint_name}': {e}")

    def unregister_blueprints(self):
        for name, blueprint in list(self.app.blueprints.items()):
            print(f"Unregistering blueprint: {name}")
            self.app.blueprints.pop(name)

    def reload_blueprints(self):
        self.unregister_blueprints()
        self.register_blueprints()

    def print_registered_blueprints(self):
        print("Registered blueprints")
        for name, blueprint in self.app.blueprints.items():
            url_prefix = self.app.blueprint_url_prefixes.get(name, 'No URL prefix set')
            print(f"Name: {name}, URL prefix: {url_prefix}")
