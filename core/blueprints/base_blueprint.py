import os

from flask import Blueprint, Response, abort


class BaseBlueprint(Blueprint):
    def __init__(
        self,
        name,
        import_name,
        static_folder=None,
        static_url_path=None,
        template_folder=None,
        url_prefix=None,
        subdomain=None,
        url_defaults=None,
        root_path=None,
    ):
        super().__init__(
            name,
            import_name,
            static_folder=static_folder,
            static_url_path=static_url_path,
            template_folder=template_folder,
            url_prefix=url_prefix,
            subdomain=subdomain,
            url_defaults=url_defaults,
            root_path=root_path,
        )
        self.module_path = os.path.join(os.getenv("WORKING_DIR", ""), "app", "modules", name)
        self.add_asset_routes()

    def add_asset_routes(self):
        """Define a dynamic route to serve any file inside subfolders under assets (e.g., js, css)."""
        assets_folder = os.path.join(self.module_path, "assets")
        if os.path.exists(assets_folder):
            # Define a route for any file inside the 'assets' folder and its subfolders
            self.add_url_rule(
                f"/{self.name}/<path:subfolder>/<path:filename>",
                "assets",
                self.send_file,
            )
        else:
            print(f"(BaseBlueprint) -> {assets_folder} does not exist.")

    def send_file(self, subfolder, filename):
        """Send any file located in the specified subfolder within the assets folder."""
        file_path = os.path.join(self.module_path, "assets", subfolder, filename)

        if filename == "webpack.config.js":
            abort(403, description="Access to this file is forbidden")

        # Check if the file exists and is located within a valid subfolder (e.g., js, css)
        if os.path.exists(file_path) and subfolder in ["js", "css", "dist"]:
            try:
                # Detect the correct MIME type based on file extension
                if filename.endswith(".js"):
                    mimetype = "application/javascript"
                elif filename.endswith(".css"):
                    mimetype = "text/css"
                else:
                    mimetype = "text/plain"

                with open(file_path, "r") as file:
                    file_content = file.read()
                return Response(file_content, mimetype=mimetype)
            except FileNotFoundError:
                abort(404, description=f"File not found: {file_path}")
        else:
            abort(404, description=f"Invalid path or file: {subfolder}/{filename}")
