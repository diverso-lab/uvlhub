from flask import Blueprint, Response
import os


class BaseBlueprint(Blueprint):
    def __init__(self, name, import_name, static_folder=None, static_url_path=None,
                 template_folder=None, url_prefix=None, subdomain=None,
                 url_defaults=None, root_path=None):
        super().__init__(name, import_name, static_folder=static_folder,
                         static_url_path=static_url_path, template_folder=template_folder,
                         url_prefix=url_prefix, subdomain=subdomain,
                         url_defaults=url_defaults, root_path=root_path)
        self.module_path = os.path.join(os.getenv('WORKING_DIR', ''), 'app', 'modules', name)
        self.add_script_route()

    def add_script_route(self):
        script_path = os.path.join(self.module_path, 'assets', 'scripts.js')
        if os.path.exists(script_path):
            self.add_url_rule(f'/{self.name}/scripts.js', 'scripts', self.send_script)
        else:
            print(f"(BaseBlueprint) -> {script_path} does not exist.")

    def send_script(self):
        script_path = os.path.join(self.module_path, 'assets', 'scripts.js')

        try:
            with open(script_path, 'r') as file:
                script_content = file.read()
            return Response(script_content, mimetype='application/javascript')
        except FileNotFoundError:
            return Response(f"File not found: {script_path}", status=404)
